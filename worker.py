import os
import time
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Inizializziamo l'applicazione Celery
celery_app = Celery("cloven_worker", broker=broker_url, backend=broker_url)

# Configuriamo il worker per essere resiliente
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
        # In un setup reale qui importeresti: process_pdf(file_path) e db.add_documents()
        
        # Simuliamo un processo pesante bloccante (es. embedding di 100 pagine)
        print(f"Starting elaboration of: {filename}")
        time.sleep(10) # <-- FastAPI timeout here, Celery no. TODO remove
        
        print(f"Elaboration of {filename} completed. Vectors saved in ChromaDB.")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return {"status": "success", "filename": filename, "message": "Document ingested"}
        
    except Exception as e:
        print(f"Error during elaboration: {str(e)}")
        return {"status": "error", "message": str(e)}