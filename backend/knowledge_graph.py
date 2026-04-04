import os
import json
import threading
import networkx as nx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Storage path
GRAPH_STORE_PATH = "uploads/contracts/graph_store.json"

# Controls how many chunks are batched into a single LLM call
BATCH_SIZE = 5

# Hard cap on total chunks processed per document — avoids runaway costs on huge contracts
MAX_CHUNKS = 40

# Lock to avoid concurrent writes to the graph file
_graph_lock = threading.Lock()


class Triple(BaseModel):
    subject: str = Field(description="The subject entity")
    predicate: str = Field(description="The relationship action or state")
    object_: str = Field(description="The object entity or value")


class ExtractionResult(BaseModel):
    triples: List[Triple] = Field(description="Extracted list of relationships")


def get_llm():
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", "dummy_key_replace_me"),
        model="google/gemini-2.5-pro",
        temperature=0
    )


def extract_triples_from_batch(batch_text: str) -> List[Triple]:
    """Send a single (possibly multi-chunk) batch to the LLM for triple extraction."""
    llm = get_llm().with_structured_output(ExtractionResult)
    prompt = PromptTemplate.from_template(
        "Extract key entities, rules, relationships and obligations from the following contract text "
        "as knowledge graph triples (subject, predicate, object).\n\n"
        "Focus on: Vendor names, roles, services, SLAs, payment terms, penalties, and numerical thresholds.\n\n"
        "Text to analyze:\n{text}"
    )
    chain = prompt | llm
    try:
        res = chain.invoke({"text": batch_text})
        return res.triples
    except Exception as e:
        print(f"[KnowledgeGraph] Batch extraction failed: {e}")
        return []


def save_graph(graph: nx.DiGraph, path: str = GRAPH_STORE_PATH):
    data = nx.node_link_data(graph)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_graph(path: str = GRAPH_STORE_PATH) -> nx.DiGraph:
    if not os.path.exists(path):
        return nx.DiGraph()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return nx.node_link_graph(data)
    except Exception as e:
        print(f"[KnowledgeGraph] Error loading graph: {e}")
        return nx.DiGraph()


def _build_graph_worker(chunks: List[str]):
    """
    Runs in a background thread.
    Caps at MAX_CHUNKS, batches BATCH_SIZE chunks per LLM call.
    """
    capped = chunks[:MAX_CHUNKS]
    total_batches = (len(capped) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"[KnowledgeGraph] Starting — {len(capped)} chunks, {total_batches} LLM batch(es) of {BATCH_SIZE}")

    with _graph_lock:
        graph = load_graph()

    for i in range(0, len(capped), BATCH_SIZE):
        batch = capped[i: i + BATCH_SIZE]
        batch_text = "\n\n---\n\n".join(batch)
        batch_num = i // BATCH_SIZE + 1
        print(f"[KnowledgeGraph] Processing batch {batch_num}/{total_batches}...")

        triples = extract_triples_from_batch(batch_text)
        with _graph_lock:
            graph = load_graph()  # Re-load to pick up any parallel updates
            for t in triples:
                subj = t.subject.strip()
                obj = t.object_.strip()
                pred = t.predicate.strip().lower()
                # Avoid huge blob strings becoming nodes
                if len(subj) < 120 and len(obj) < 120 and subj and obj:
                    graph.add_edge(subj, obj, relation=pred)
            save_graph(graph)

    print(f"[KnowledgeGraph] Done — graph now has {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")


def build_contract_graph_from_chunks(chunks: List[str]):
    """
    Kicks off KG extraction in a background thread so the upload
    endpoint returns immediately without waiting for LLM calls.
    """
    t = threading.Thread(target=_build_graph_worker, args=(chunks,), daemon=True)
    t.start()
    print(f"[KnowledgeGraph] Background extraction started for {len(chunks)} chunks (capped at {MAX_CHUNKS}).")


def query_graph(query_entity: str) -> str:
    """Return relationships related to an entity that keyword-matches in the graph."""
    graph = load_graph()

    if graph.number_of_nodes() == 0:
        return "Knowledge Graph is still being built or is empty. Try again shortly."

    query_lower = query_entity.lower()
    matched_nodes = [
        n for n in graph.nodes
        if isinstance(n, str) and query_lower in n.lower()
    ]

    related_edges = []
    for node in matched_nodes:
        for u, v, data in graph.edges(node, data=True):
            related_edges.append(f"[{u}] -> ({data.get('relation', 'related to')}) -> [{v}]")
        for u, v, data in graph.in_edges(node, data=True):
            edge_str = f"[{u}] -> ({data.get('relation', 'related to')}) -> [{v}]"
            if edge_str not in related_edges:
                related_edges.append(edge_str)

    if not related_edges:
        return f"No graph relationships found for '{query_entity}'."

    # Deduplicate, cap at 25 results to avoid token overload
    return "\n".join(list(set(related_edges))[:25])
