from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_engine import ask_document
from fastapi import UploadFile, File
import os
import shutil
import re
from worker import process_document_task

def sanitize_filename(filename: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z0-9.\-]', '_', filename)
    return re.sub(r'_+', '_', clean_name)

app = FastAPI(
    title="Cloven Viscount API",
    description="testing APIs for the Cloven Viscount",
    version="1.0"
)

# print("Initializing RAG Engine on server startup...")
# rag_chain = setup_rag_chain()

@app.get("/")
def base_route():
    return {"message": "FastAPI server is active and working!"}

# @app.post("/analyze")
# def analyze_data(request: requestAnalysis):
#     try:
#         answer = rag_chain.invoke(request.question)
        
#         return {
#             "status": "success",
#             "question": request.question,
#             "answer": answer
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

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
        "task_id": task.id 
        "filename_saved_as": safe_filename
    }

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat_with_document(request: ChatRequest):
    try:
        answer = ask_document(request.query)
        
        return {
            "status": "success",
            "query": request.query,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")