from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from vector_store import get_vector_database

# load secret API key from the .env file
load_dotenv()

def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def ask_document(query_text: str, history: list) -> str:
    llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant")
    
    db = get_vector_database()
    retriever = db.as_retriever(search_kwargs={"k": 3})

    chat_history = []
    for msg in history:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            chat_history.append(AIMessage(content=msg.content))
    
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    condense_question_chain = contextualize_q_prompt | llm | StrOutputParser()

    # inner function
    def get_standalone_query(x: dict) -> str:
        if x.get("chat_history"):
            return condense_question_chain.invoke({
                "input": x["input"], 
                "chat_history": x["chat_history"]
            })
        return x["input"]
    
    qa_system_prompt = (
        "You are an expert and rigorous corporate assistant. "
        "Use EXCLUSIVELY the following pieces of retrieved context to answer the user's question. "
        "If the answer is not contained in the context, do not make it up or guess. "
        "Just answer: 'I could not find this information in the provided documents.'\n\n"
        "Context:\n{context}"
    )
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    rag_chain = (
        RunnablePassthrough.assign(
            context=lambda x: format_docs(retriever.invoke(get_standalone_query(x)))
        )
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    answer = rag_chain.invoke({
        "input": query_text,
        "chat_history": chat_history
        })

    return answer

# cli __main__ test
if __name__ == "__main__":
       
    # Test the system!
    user_question = "What is the mandatory skill required to apply this position?"
    print(f"\nUser Question: {user_question}")
    print("Generating answer based on documents...\n")
    
    # We pass the input to the chain and invoke it
    response = ask_document(user_question)
    
    print("--- AI ANSWER ---")
    print(response)