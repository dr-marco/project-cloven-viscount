import chromadb
import os

# Define where your database is stored on disk
DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db_local")

def inspect_database():
    print(f"🔍 Inspecting ChromaDB at: {DB_DIR}")
    
    try:
        # Initialize the native ChromaDB client
        client = chromadb.PersistentClient(path=DB_DIR)
        
        # 1. List all collections
        collections = client.list_collections()
        if not collections:
            print("⚠️ No collections found. The database is completely empty.")
            return

        print(f"\n📂 Found {len(collections)} collection(s):")
        for col in collections:
            print(f" - {col.name}")
            
        # 2. Inspect the first collection (LangChain defaults to 'langchain')
        collection = collections[0]
        count = collection.count()
        print(f"\n📊 Collection '{collection.name}' contains {count} vector chunks.")
        
        if count > 0:
            # 3. Peek at the first 2 records
            print("\n👀 Peeking at the first 2 chunks:")
            
            # .get() retrieves documents and metadata without doing a vector search
            results = collection.get(limit=2)
            
            for i in range(len(results['ids'])):
                print(f"\n--- Chunk {i+1} ---")
                print(f"🆔 ID: {results['ids'][i]}")
                # Print only the first 200 characters of the text to avoid spamming the terminal
                print(f"📄 Text: {results['documents'][i][:200]}...") 
                print(f"🏷️ Metadata: {results['metadatas'][i]}")
                
    except Exception as e:
        print(f"❌ Error inspecting ChromaDB: {e}")
        print("Note: Ensure no other process (like Celery) is actively locking the SQLite file.")

if __name__ == "__main__":
    inspect_database()