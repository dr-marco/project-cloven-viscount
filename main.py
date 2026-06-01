from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from rag_engine import ask_document
from fastapi import UploadFile, File
import os
import shutil
import re
from worker import process_document_task, celery_app
from celery.result import AsyncResult
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from langchain.globals import set_debug
from contextlib import asynccontextmanager
from vector_store import get_vector_database

# DEBUG flag
set_debug(False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP (Warmup) ---
    print("🚀 Server inizialization - ongoing Warmup...")
    try:
        # enforce loading Embeffing model in RAM
        db = get_vector_database()
        
        # forcing ChromaDB to open and to index files
        collection_count = db._collection.count()
        print(f"✅ Warmup completed. Vectorial database ready (active collections: {collection_count}).")
    except Exception as e:
        print(f"⚠️ partial Warmup (DB could be empty or not initialized): {e}")
    
    yield
    
    # --- SHUTDOWN (Cleanup) ---
    print("🛑 Spegnimento del server in corso. Rilascio delle risorse...")

def sanitize_filename(filename: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9.\-]', '_', filename)
    return re.sub(r'_+', '_', clean_name)

app = FastAPI(
    title="Cloven Viscount API",
    lifespan=lifespan
)

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/")
def base_route():
    return {"message": "FastAPI server is active and working!"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    safe_filename = sanitize_filename(file.filename)

    os.makedirs("data", exist_ok=True)
    file_path = f"data/{safe_filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    task = process_document_task.delay(file_path, file.filename)
    
    return {
        "status": "accepted", 
        "message": "Document added in elaboration queue.",
        "task_id": task.id,
        "filename_saved_as": safe_filename
    }

class Message(BaseModel):
    role: str      
    content: str  

class ChatRequest(BaseModel):
    query: str
    history: List[Message] = []

@app.post("/chat")
@limiter.limit("5/minute")
async def chat_with_document(request: Request, payload: ChatRequest):
    try:
        answer = ask_document(payload.query, payload.history)
        return {"query": payload.query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Query Redis to check the status of the Celery task.
    Possible states: PENDING, STARTED, SUCCESS, FAILURE.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": str(task_result.result) if task_result.ready() else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")

@app.get("/db-status")
async def get_db_status():
    """
    Check if the database has some documents saved or if it is empty 
    """
    try:
        db = get_vector_database()
        count = db._collection.count()
        return {
            "has_documents": count > 0, 
            "document_count": count
        }
    except Exception as e:
        return {"has_documents": False, "document_count": 0}