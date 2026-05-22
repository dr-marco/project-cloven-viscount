import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
# from langchain.chains import create_retrieval_chain
# from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from vector_store import get_vector_database

# 1. Load the secret API key from the .env file
load_dotenv()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def setup_rag_chain():
    """
    Initializes the LLM, connects it to ChromaDB, and creates the question-answering chain.
    """
    # 2. Initialize the LLM (using the blazing fast Llama 3 model via Groq)
    # The api_key is automatically loaded from the environment variable GROQ_API_KEY
    llm = ChatGroq(
        model_name="llama-3.1-8b-instant", 
        temperature=0.0  # 0.0 means deterministic answers (no creative hallucinations)
    )

    # 3. Load our previously built Vector Database
    db = get_vector_database()
    
    # We turn the database into a "retriever" (an interface LangChain can use to query it)
    # k=3 means "retrieve the top 3 most relevant chunks to answer the user"
    retriever = db.as_retriever(search_kwargs={"k": 3})

    template = """You are an expert HR assistant helping a person looking for a job.
    Use the following pieces of retrieved context to answer the question.
    If the answer is not in the context, say 'I don't have this information in the document'.
    Keep the answer concise and professional.

    Context: {context}

    Question: {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # . Build the LCEL Chain (LangChain Expression Language)
    # This reads exactly like a pipeline: 
    # Fetch docs -> Format them -> Inject into Prompt -> Send to LLM -> Parse Output as String
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain

if __name__ == "__main__":
    print("Initializing RAG System...")
    chain = setup_rag_chain()
    
    # Test the system!
    user_question = "What is the mandatory skill required to apply this position?"
    print(f"\nUser Question: {user_question}")
    print("Generating answer based on documents...\n")
    
    # We pass the input to the chain and invoke it
    response = chain.invoke(user_question)
    
    print("--- AI ANSWER ---")
    print(response)