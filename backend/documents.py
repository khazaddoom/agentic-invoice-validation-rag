import os
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from knowledge_graph import build_contract_graph_from_chunks

CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Use lightweight local embeddings
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def get_vector_store():
    return Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def process_document(file_path: str, config: dict = None):
    """
    Extracts text from a document, chunks it using enabled strategies, and adds to VectorDB.
    """
    if config is None:
        config = {"enabled_strategies": ["recursive"]}

    # 1. Extract text
    if file_path.endswith('.pdf'):
        raw_text = extract_text_from_pdf(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
    vector_store = get_vector_store()
    total_chunks = 0
            
    # 2. Iterate Strategies
    enabled_strategies = config.get("enabled_strategies", [])
    for strategy in enabled_strategies:
        chunks = []
        if strategy == "semantic":
            text_splitter = SemanticChunker(embeddings)
            chunks_docs = text_splitter.create_documents([raw_text])
            chunks = [doc.page_content for doc in chunks_docs]
        elif strategy == "recursive":
            params = config.get("chunking_parameters", {}).get("recursive", {})
            chunk_size = params.get("chunk_size", 1000)
            chunk_overlap = params.get("chunk_overlap", 200)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len
            )
            chunks = text_splitter.split_text(raw_text)
            
            # Use recursive chunks to build Knowledge Graph (only once per document)
            try:
                build_contract_graph_from_chunks(chunks)
            except Exception as e:
                print(f"Failed to build Knowledge Graph: {e}")
            
        if chunks:
            # Associate metadata with the chunks
            metadatas = [{"source": file_path, "strategy": strategy} for _ in chunks]
            vector_store.add_texts(texts=chunks, metadatas=metadatas)
            total_chunks += len(chunks)
            
    return total_chunks    
