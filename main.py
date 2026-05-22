from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_engine import setup_rag_chain
from fastapi import UploadFile, File
import os
import shutil
from document_processor import process_pdf
from vector_store import get_vector_database

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
    return {"messagge": "FastAPI server is active and working!"}

@app.post("/analyze")
def analyze_data(request: requestAnalysis):
    try:
        # Passiamo la domanda dell'utente alla catena LCEL
        answer = rag_chain.invoke(request.question)
        
        return {
            "status": "success",
            "question": request.question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # return {
    #     "status": "success",
    #     "received_data": {
    #         "cv_length": len(request.text_cv),
    #         "role": request.desired_role
    #     },
    #     "message": "Data received successfully. (AI not implemented yet)"
    # }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    
    # 1. Verifica che sia un PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    # 2. Salva il file fisicamente dentro il container
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 3. Usa lo script dello Sprint 2 per tagliare il PDF in chunk
        chunks = process_pdf(file_path)
        
        # 4. Ottieni l'istanza del database Chroma e aggiungi i nuovi chunk
        db = get_vector_database()
        db.add_documents(chunks)
        
        return {
            "status": "success", 
            "message": f"File '{file.filename}' elaborated correctly.",
            "chunks_added": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during PDF elaboration: {str(e)}")