import os
import json
import networkx as nx
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List

# Ensure storage directory
GRAPH_STORE_PATH = "uploads/contracts/graph_store.json"

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
    
def extract_triples_from_text(text: str) -> List[Triple]:
    llm = get_llm().with_structured_output(ExtractionResult)
    prompt = PromptTemplate.from_template(
        "Extract key entities, rules, relationships and obligations from the following contract text as knowledge graph triples (subject, predicate, object).\n\n"
        "Focus on: Vendor names, roles, services, Service Level Agreements (SLAs), terms, penalties, or numerical thresholds.\n\n"
        "Text to analyze:\n{text}"
    )
    chain = prompt | llm
    try:
        res = chain.invoke({"text": text})
        return res.triples
    except Exception as e:
        print(f"Extraction failed: {e}")
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
        print(f"Error loading graph: {e}")
        return nx.DiGraph()

def build_contract_graph_from_chunks(chunks: List[str]):
    """ Extract graph from text chunks and merge into global store """
    graph = load_graph()
    
    # Process chunks in batch or iteratively. We'll do it iteratively.
    for text in chunks:
        triples = extract_triples_from_text(text)
        for t in triples:
            # Normalize to avoid Case Sensitivity issues (simple approach)
            subj = t.subject.strip()
            obj = t.object_.strip()
            pred = t.predicate.strip().lower()
            
            # Avoid adding massive text as nodes
            if len(subj) < 100 and len(obj) < 100:
                graph.add_edge(subj, obj, relation=pred)
                
    save_graph(graph)

def query_graph(query_entity: str) -> str:
    """ Return relationships related to a target entity or concept roughly matching query. """
    graph = load_graph()
    
    query_entity_lower = query_entity.lower()
    
    related_edges = []
    # Simple keyword search over nodes
    matched_nodes = [n for n in graph.nodes if isinstance(n, str) and query_entity_lower in n.lower()]
    
    for node in matched_nodes:
        # Get edges in and out
        for u, v, data in graph.edges(node, data=True):
            relation = data.get("relation", "is related to")
            related_edges.append(f"[{u}] -> ({relation}) -> [{v}]")
            
        for u, v, data in graph.in_edges(node, data=True):
            relation = data.get("relation", "is related to")
            # Avoid dupes slightly
            edge_str = f"[{u}] -> ({relation}) -> [{v}]"
            if edge_str not in related_edges:
                related_edges.append(edge_str)
                
    if not related_edges:
        return f"No direct graph relationships found for entity matching '{query_entity}'."
    
    # Deduplicate and return at most 20 to avoid token overload
    return "\n".join(list(set(related_edges))[:20])
