import os
from celery import Celery
from document_processor import process_pdf
from vector_store import get_vector_database

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Celery app initialization
celery_app = Celery("cloven_worker", broker=broker_url, backend=broker_url)

# worker configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Rome',
    enable_utc=True,
)

@celery_app.task(name="process_document_task")
def process_document_task(file_path: str, filename: str):
    try:
        print(f"Starting elaboration of: {filename}")
        
        chunks = process_pdf(file_path)
        print(f"Estracted {len(chunks)} segments from document.")
        
        db = get_vector_database()
        db.add_documents(chunks)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        print(f"Elaboration of {filename} completed. Vectors saved.")
        return {"status": "success", "filename": filename, "chunks": len(chunks)}
        
    except Exception as e:
        print(f"Critic error during elaboration of {filename}: {str(e)}")
        return {"status": "error", "message": str(e)}