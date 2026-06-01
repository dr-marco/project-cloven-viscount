import streamlit as st
import requests
import time

# Page configuration
st.set_page_config(page_title="Cloven Viscount RAG", page_icon="🗡️", layout="wide")

# Backend URL (FastAPI runs on port 8000 in the api_backend container)
API_BASE_URL = "http://api_backend:8000"

# --- STATE INITIALIZATION ---
# Streamlit reloads the page on every interaction. 
# We use session_state to keep track of chat history and file processing status.
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False

if "db_populated" not in st.session_state:
    try:
        res = requests.get(f"{API_BASE_URL}/db-status")
        if res.status_code == 200:
            st.session_state.db_populated = res.json().get("has_documents", False)
        else:
            st.session_state.db_populated = False
    except:
        st.session_state.db_populated = False

st.title("🗡️ Cloven Viscount - Document Intelligence")
st.markdown("Upload a PDF document and ask questions to the RAG model.")

if st.session_state.db_populated or st.session_state.file_processed:
    st.info("ℹ️ The database already contains documents. You can ask questions or upload a new PDF to enrich the knowledge base.")
else:
    st.warning("⚠️ Warning: Please make sure to upload and process a document before asking questions.")

# --- SIDEBAR: UPLOAD MANAGEMENT ---
with st.sidebar:
    st.header("Document Ingestion")
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Uploading document to server..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        task_id = data.get('task_id')
                        st.info(f"Task ID: {task_id} generated. Starting processing...")
                        
                        status = "PENDING"
                        status_placeholder = st.empty() 
                        
                        while status not in ["SUCCESS", "FAILURE"]:
                            status_placeholder.info(f"Current status: {status}... querying backend.")
                            time.sleep(2) 
                            
                            status_response = requests.get(f"{API_BASE_URL}/task-status/{task_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                status = status_data.get("status")
                            else:
                                st.error("Error communicating with the backend status endpoint.")
                                break
                        
                        status_placeholder.empty() 
                        if status == "SUCCESS":
                            st.success("✅ Document processed successfully! You can now ask questions.")
                            st.session_state.file_processed = True
                        elif status == "FAILURE":
                            st.error("❌ There was an error processing the document by the worker.")
                            
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Backend connection error: {e}")

# --- MAIN AREA: CHAT INTERFACE ---

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask a question about the uploaded document..."):
    if not (st.session_state.db_populated or st.session_state.file_processed):
        st.error("Operation blocked: upload a document before query.")
        st.stop()

    # 1. Add user question to the UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call the backend API
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating response..."):
            try:
                # Call our new /chat endpoint
                past_history = st.session_state.messages[:-1]
                
                payload = {
                    "query": prompt,
                    "history": past_history
                }
                
                response = requests.post(f"{API_BASE_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    answer = response.json().get("answer", "No response received.")
                    st.markdown(answer)
                    # Save the response in the chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"Backend error: {response.text}")
            except Exception as e:
                st.error(f"Backend connection error: {e}")