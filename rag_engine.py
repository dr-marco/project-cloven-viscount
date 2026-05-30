from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from vector_store import get_vector_database

# 1. Load the secret API key from the .env file
load_dotenv()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def ask_document(query_text: str) -> str:
    llm = ChatGroq(temperature=0, model_name="llama3-8b-8192")
    
    db = get_vector_database()
    retriever = db.as_retriever(search_kwargs={"k": 3})

    system_prompt = (
        "You are an expert and rigorous corporate assistant. "
        "Use EXCLUSIVELY the following pieces of retrieved context to answer the user's question. "
        "If the answer is not contained in the context, do not make it up or guess. "
        "Just answer: 'I could not find this information in the provided documents.'\n\n"
        "Context:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 5. Invoca la catena
    return rag_chain

if __name__ == "__main__":
       
    # Test the system!
    user_question = "What is the mandatory skill required to apply this position?"
    print(f"\nUser Question: {user_question}")
    print("Generating answer based on documents...\n")
    
    # We pass the input to the chain and invoke it
    response = ask_document(user_question)
    
    print("--- AI ANSWER ---")
    print(response)