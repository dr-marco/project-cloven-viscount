from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_pdf(file_path: str):
    """
    Loads a PDF file and splits it into manageable text chunks.
    """
    # 1. Load the document
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    # 2. Configure the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,       # Number of characters per chunk
        chunk_overlap=200,     # Number of characters overlapping between chunks
        length_function=len,
        is_separator_regex=False,
    )
    
    # 3. Split the text
    chunks = text_splitter.split_documents(documents)
    
    return chunks

# CLI execution
if __name__ == "__main__":
    test_pdf_path = "data/sample-job.pdf"
    
    try:
        resulting_chunks = process_pdf(test_pdf_path)
        print(f"Successfully split the PDF into {len(resulting_chunks)} chunks.")
        
        # Print first 200 characters for test purpouse
        if resulting_chunks:
            print("\nPreview of Chunk 1:")
            print(resulting_chunks[0].page_content[:200] + "...")
            
    except Exception as e:
        print(f"Error processing PDF: {e}")