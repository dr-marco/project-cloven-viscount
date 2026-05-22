from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from document_processor import process_pdf
import os

# Define where to save the database on disk
DB_DIR = "/app/chroma_db"

def build_vector_database(file_path: str):
    """
    Processes a PDF, converts chunks to embeddings, and saves them to ChromaDB.
    """
    print(f"Loading and chunking {file_path}...")
    chunks = process_pdf(file_path)
    
    # Initialize the embedding model (downloads a lightweight model locally on first run)
    print("Initializing embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Create and persist the vector database
    print("Building Vector Database...")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    
    print("Database built successfully!")
    return vector_db

def get_vector_database():
    """
    Loads an existing vector database from disk.
    """
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

if __name__ == "__main__":
    # Test path from Sprint 2
    test_pdf_path = "data/sample-job.pdf"
    
    # 1. Build the database
    db = build_vector_database(test_pdf_path)
    
    # 2. Test a Semantic Search (Similarity Search)
    query = "What is the mandatory skill required to apply this position?"
    print(f"\nSearching for: '{query}'")
    
    # k=2 means we want the top 2 most relevant chunks
    results = db.similarity_search(query, k=2) 
    
    print("\nTop Results Found:")
    for i, res in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(res.page_content)