import os
import redis
from celery import Celery
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Your local imports
from document_processor import process_pdf
from vector_store import get_vector_database

# Broker configuration
broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis_broker:6379/0")

# Redis configuration
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis_broker:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Celery app initialization
celery_app = Celery("cloven_worker", broker=broker_url, backend=broker_url)

# Worker configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Rome',
    enable_utc=True,
)

ASYNC_DB_URL = os.environ.get("DATABASE_URL")
if ASYNC_DB_URL:
    SYNC_DB_URL = ASYNC_DB_URL.replace("+asyncpg", "")
    sync_engine = create_engine(SYNC_DB_URL)
    SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def update_document_status_sync(document_id: str, new_status: str):
    try:
        with SyncSessionLocal() as session:
            session.execute(
                text("UPDATE documents SET status = :status WHERE id = :id"),
                {"status": new_status, "id": document_id}
            )
            session.commit()
    except Exception as e:
        print(f"Error during DB update: {e}")

def update_redis_progress(document_id: str, status_code: str, message: str):
    """Write status with Redis with 1 hour espiration time"""
    payload = f"{status_code}|{message}" # Es: "PROCESSING|Estrazione testo in corso..."
    redis_client.setex(f"progress:{document_id}", 3600, payload)

@celery_app.task(name="process_document_task")
def process_document_task(file_path: str, filename: str, document_id: str):
    try:
        print(f"Starting elaboration of: {filename} (UUID: {document_id})")
        
        # 1. Use your existing custom processor
        update_redis_progress(document_id, "PROCESSING", "Preso in carico dal worker. Estrazione testo...")
        chunks = process_pdf(file_path)
        print(f"Extracted {len(chunks)} segments from document.")
        update_redis_progress(document_id, "PROCESSING", "Testo estratto. Caricamento in ChromaDB...")
        
        # 2. INJECTION: Tying the semantic vectors to the relational database
        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            chunk.metadata["source_file"] = filename
            
        # 3. Save to ChromaDB
        db = get_vector_database()
        db.add_documents(chunks)
        
        # 4. Clean up the physical file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 5. UPDATE STATE IN POSTGRESQL to 'COMPLETED'
        # Celery is synchronous, so we run the async function via asyncio.run()
        update_redis_progress(document_id, "SUCCESS", "Elaborazione completata con successo!")
        update_document_status_sync(document_id, "COMPLETED")
            
        print(f"Elaboration of {filename} completed. Vectors saved and DB updated.")
        return {"status": "success", "filename": filename, "chunks": len(chunks), "document_id": document_id}
        
    except Exception as e:
        print(f"Critical error during elaboration of {filename}: {str(e)}")
        
        # UPDATE STATE IN POSTGRESQL to 'FAILED'
        update_redis_progress(document_id, "FAILED", f"Errore critico: {str(e)}")
        update_document_status_sync(document_id, "FAILED")
        return {"status": "error", "message": str(e)}