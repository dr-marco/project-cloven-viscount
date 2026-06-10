import os
import shutil
import re
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends, status
from pydantic import BaseModel
from typing import List
from celery.result import AsyncResult
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
import redis

# Local imports
from rag_engine import ask_document
from worker import process_document_task, celery_app
from vector_store import get_vector_database
from database import get_db
from models import Document

import uuid
from sqlalchemy import select

# Initialize Router and Limiter
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

redis_client = redis.Redis.from_url(os.environ.get("CELERY_BROKER_URL", "redis://redis_broker:6379/0"), decode_responses=True)

def sanitize_filename(filename: str) -> str:
    """Removes unsupported characters from the filename."""
    clean_name = re.sub(r'[^a-zA-Z0-9.\-]', '_', filename)
    return re.sub(r'_+', '_', clean_name)

class Message(BaseModel):
    role: str      
    content: str  

class ChatRequest(BaseModel):
    query: str
    history: List[Message] = []

@router.get("/")
def base_route():
    return {"message": "FastAPI server is active and working!"}

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handles file upload, registers a PENDING record in PostgreSQL,
    and delegates the heavy embedding extraction to Celery.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    safe_filename = sanitize_filename(file.filename)

    try:
        # 1. Create a new Document record in PostgreSQL
        new_doc = Document(
            filename=safe_filename,
            status="PENDING"
        )
        
        # 2. Save to the relational database
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        # 3. Save the file physically
        os.makedirs("data", exist_ok=True)
        file_path = f"data/{safe_filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 4. Trigger Celery task (passing the new UUID as a string)
        task = process_document_task.delay(
            file_path=file_path, 
            filename=safe_filename,
            document_id=str(new_doc.id) 
        )
        
        return {
            "status": "accepted", 
            "message": "Document added to the elaboration queue.",
            "task_id": task.id,
            "document_id": str(new_doc.id),
            "filename_saved_as": safe_filename
        }

    except Exception as e:
        # Rollback the transaction in case of any failure
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during document registration: {str(e)}"
        )

@router.post("/chat")
@limiter.limit("5/minute")
async def chat_with_document(request: Request, payload: ChatRequest):
    try:
        answer = ask_document(payload.query, payload.history)
        return {"query": payload.query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Query Redis to check the status of the Celery task.
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

@router.get("/db-status")
async def get_db_status():
    """
    Check if the database has some documents saved or if it is empty.
    """
    try:
        db = get_vector_database()
        count = db._collection.count()
        return {
            "has_documents": count > 0, 
            "document_count": count
        }
    except Exception:
        return {"has_documents": False, "document_count": 0}

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Hard delete: Removes the document from the PostgreSQL registry
    and purges all associated vector embeddings from ChromaDB.
    """
    try:
        # 1. Validate UUID format to prevent malformed queries
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid document ID format. Must be a valid UUID."
        )

    try:
        # 2. Check if the document exists in PostgreSQL
        stmt = select(Document).where(Document.id == doc_uuid)
        result = await db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=404, 
                detail="Document not found in the SQL registry."
            )

        # 3. Purge vectors from ChromaDB (The Semantic Memory)
        # We access the underlying native ChromaDB collection to use the metadata filter
        vector_db = get_vector_database()
        vector_db._collection.delete(
            where={"document_id": document_id}
        )
        print(f"🧹 Purged vectors from ChromaDB for document: {document_id}")

        # 4. Delete the record from PostgreSQL (The Administrative Memory)
        await db.delete(document)
        await db.commit()
        
        # 5. Clean up the physical file (Optional but recommended)
        file_path = f"data/{document.filename}"
        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "status": "success",
            "message": f"Document '{document.filename}' and its associated vectors have been completely removed."
        }

    except HTTPException:
        # Re-raise standard HTTP exceptions (like 404 or 400) so they don't get swallowed
        raise
    except Exception as e:
        # If ChromaDB or anything else fails, rollback the SQL transaction 
        # so we don't end up with an inconsistent state
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during hard deletion: {str(e)}"
        )

@router.get("/document-status/{document_id}")
def get_document_progress(document_id: str):
    """Endpoint ultra-veloce che legge il tabellone di Redis invece di pesare su SQL/Celery"""
    raw_status = redis_client.get(f"progress:{document_id}")
    
    if not raw_status:
        # Se Redis non ha nulla, significa che il worker non è ancora partito
        return {"task_status": "PENDING", "message": "In attesa di un worker libero..."}
    
    # Dividiamo il codice dalla stringa descrittiva (es: "PROCESSING|Estrazione testo...")
    status_parts = raw_status.split("|", 1)
    status_code = status_parts[0]
    message = status_parts[1] if len(status_parts) > 1 else ""
    
    return {"task_status": status_code, "message": message}