from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_engine import setup_rag_chain
from fastapi import UploadFile, File
import os
import shutil
from document_processor import process_pdf
from vector_store import get_vector_database
from worker import process_document_task

app = FastAPI(
    title="Cloven Viscount API",
    description="testing APIs for the Cloven Viscount",
    version="1.0"
)

print("Initializing RAG Engine on server startup...")
rag_chain = setup_rag_chain()

class requestAnalysis(BaseModel):
    question: str

@app.get("/")
def base_route():
    return {"message": "FastAPI server is active and working!"}

@app.post("/analyze")
def analyze_data(request: requestAnalysis):
    try:
        answer = rag_chain.invoke(request.question)
        
        return {
            "status": "success",
            "question": request.question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # Salva il file temporaneamente
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    task = process_document_task.delay(file_path, file.filename)
    
    return {
        "status": "accepted", 
        "message": "Il documento è stato messo in coda per l'elaborazione.",
        "task_id": task.id 
    }


# @app.post("/upload")
# async def upload_document(file: UploadFile = File(...)):
    
#     # 1. Verifica che sia un PDF
#     if not file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
#     # 2. Salva il file fisicamente dentro il container
#     os.makedirs("data", exist_ok=True)
#     file_path = f"data/{file.filename}"
    
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
        
#     try:
#         # 3. Usa lo script dello Sprint 2 per tagliare il PDF in chunk
#         chunks = process_pdf(file_path)
        
#         # 4. Ottieni l'istanza del database Chroma e aggiungi i nuovi chunk
#         db = get_vector_database()
#         db.add_documents(chunks)
        
#         return {
#             "status": "success", 
#             "message": f"File '{file.filename}' elaborated correctly.",
#             "chunks_added": len(chunks)
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error during PDF elaboration: {str(e)}")