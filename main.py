from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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

def sanitize_filename(filename: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9.\-]', '_', filename)
    return re.sub(r'_+', '_', clean_name)

app = FastAPI(
    title="Cloven Viscount API"
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

    # Salva il file temporaneamente
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

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
@limiter.limit("5/minute")
async def chat_with_document(request: Request, payload: ChatRequest):
    try:
        answer = ask_document(request.query)
        return {"query": payload.query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Interroga Redis per scoprire a che punto è il task di Celery.
    I possibili stati sono: PENDING, STARTED, SUCCESS, FAILURE.
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": task_result.status,
            # result conterrà il valore di ritorno della funzione Celery se SUCCESS, 
            # o l'errore se FAILURE.
            "result": str(task_result.result) if task_result.ready() else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel recupero stato: {str(e)}")