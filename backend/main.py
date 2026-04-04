from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
import json

from documents import process_document
from agent import validate_invoice

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "enabled_strategies": ["recursive", "semantic"],
    "chunking_parameters": {
        "recursive": {
            "chunk_size": 1000,
            "chunk_overlap": 200
        },
        "semantic": {
            "breakpoint_threshold_type": "percentile"
        }
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config_data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)


app = FastAPI(title="Agentic RAG Invoice Validation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads/contracts", exist_ok=True)
os.makedirs("uploads/invoices", exist_ok=True)

class ValidationRequest(BaseModel):
    invoice_path: str

@app.get("/")
def read_root():
    return {"status": "ok"}
@app.get("/api/config")
def get_config():
    return load_config()

@app.post("/api/config")
def update_config(config: dict):
    save_config(config)
    return {"status": "updated"}

@app.post("/api/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_location = f"uploads/contracts/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
    # Process into Vector DB using Ensemble Architecture
    try:
        config = load_config()
        chunks = process_document(file_location, config)
        return {"filename": file.filename, "status": "indexed_ensemble", "chunks": chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/invoice/upload")
async def upload_invoice(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_location = f"uploads/invoices/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)
        
    return {"filename": file.filename, "path": file_location}

@app.post("/api/invoice/validate")
async def run_validation(req: ValidationRequest):
    if not os.path.exists(req.invoice_path):
        raise HTTPException(status_code=404, detail="Invoice file not found")
        
    try:
        result = await validate_invoice(req.invoice_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
