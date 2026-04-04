import os
import difflib
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from documents import get_vector_store, extract_text_from_pdf
from dotenv import load_dotenv
from mcp_adapter import get_langchain_mcp_tools
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# We use the ChatOpenAI client pointed at OpenRouter
llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "dummy_key_replace_me"),
    model="google/gemini-2.5-pro", # Can be configured via env
)

# Global accumulator for tracking clauses used during this session
_session_retrieved_clauses = []

@tool
def search_contract_clauses(query: str) -> str:
    """
    Search the vector database for relevant contract clauses and vendor documentation.
    Use this to pull contract terms to validate against the invoice.
    """
    vector_store = get_vector_store()
    raw_contexts = []
    docs = vector_store.similarity_search(query, k=6) 
    for d in docs:
        raw_contexts.append(d.page_content)
            
    # Deduplication
    retrieved_contexts = []
    for chunk in raw_contexts:
        is_duplicate = False
        for saved_chunk in retrieved_contexts:
            if chunk in saved_chunk or saved_chunk in chunk:
                is_duplicate = True
                if len(chunk) > len(saved_chunk):
                    retrieved_contexts.remove(saved_chunk)
                    retrieved_contexts.append(chunk)
                break
            similarity = difflib.SequenceMatcher(None, chunk, saved_chunk).ratio()
            if similarity > 0.75:
                is_duplicate = True
                if len(chunk) > len(saved_chunk):
                    retrieved_contexts.remove(saved_chunk)
                    retrieved_contexts.append(chunk)
                break
        if not is_duplicate:
            retrieved_contexts.append(chunk)
            
    global _session_retrieved_clauses
    _session_retrieved_clauses.extend(retrieved_contexts)
    
    return "\n\n---\n\n".join(retrieved_contexts) if retrieved_contexts else "No relevant clauses found."

async def validate_invoice(invoice_path: str):
    """
    Agentic workflow to validate an invoice against the knowledge base and MCP extensions.
    """
    global _session_retrieved_clauses
    _session_retrieved_clauses = []
    
    # 1. Extract Invoice text
    if invoice_path.endswith('.pdf'):
        invoice_text = extract_text_from_pdf(invoice_path)
    else:
        with open(invoice_path, "r", encoding="utf-8") as f:
            invoice_text = f.read()

    # 2. Gather MCP Tools (dynamically)
    mcp_tools = await get_langchain_mcp_tools()
    
    # 3. Create tool list
    agent_tools = [search_contract_clauses] + mcp_tools
    
    # 4. System prompt enforcing the final schema output
    system_prompt = """You are an expert contract auditor. You must validate if the provided invoice safely adheres to contract terms and external validation rules.
Use the `search_contract_clauses` tool to search for terms mentioned in the invoice (like vendor names, services, SLAs).
If available, also use external validation tools like `get_external_business_rules` (if provided via MCP) to fetch any overarching system rules that might apply to this vendor or invoice.
IMPORTANT: Do not guess. You must actually call the search tools to retrieve the contract before deciding.

Once you have gathered enough information, you MUST output your the report strictly in Markdown format, following EXACTLY this structure:

### 1. Validation Context
[Provide a brief context of the vendor, dates, and purpose of the invoice based on your searches.]

### 2. Audit Checklist & Findings
| Item Checked | Contract Clause / Reference | Finding | Status |
|---|---|---|---|
| [Item] | [Reference] | [Description] | [Discrepancy / Observation / Adheres / Observation (not verifiable)] |

*(Log every checked item as a separate row in the table above. Include findings from both Contract clauses AND External business rules if used.)*

### 3. Summary
[Provide a high-level summary of the compliance check.]

### 4. Final Conclusion / Recommendation
**Adherence Rating:** [Provide a 5-Star rating using actual star symbols, e.g., ★★★★☆]

[Provide the final [ADHERES] or [DOES NOT ADHERE] evaluation and concrete next steps.]"""

    # 5. Execute React Agent
    agent = create_react_agent(llm, agent_tools, prompt=system_prompt)
    
    messages = [HumanMessage(content=f"Please validate this invoice text:\n\n{invoice_text}")]
    result = await agent.ainvoke({"messages": messages})
    
    final_report = result["messages"][-1].content
    
    # Extract MCP tool usage
    mcp_used = []
    for msg in result["messages"]:
        if getattr(msg, "name", "") == "get_external_business_rules" or msg.type == "tool":
             if getattr(msg, "name", "") == "get_external_business_rules":
                 mcp_used.append(msg.content)
    
    # Also fetch available
    try:
        from mcp_adapter import execute_mcp_tool
        available = await execute_mcp_tool("get_external_business_rules", {})
    except:
        available = "None"
    
    # Deduplicate _session_retrieved_clauses for the final view
    final_clauses = list(set(_session_retrieved_clauses))

    return {
        "invoice_extracted_text": invoice_text,
        "retrieved_clauses": final_clauses,
        "mcp_rules_used": list(set(mcp_used)),
        "mcp_rules_available": available,
        "validation_report": final_report
    }
