import streamlit as st
import requests
import time

# Page configuration
st.set_page_config(page_title="Cloven Viscount RAG", page_icon="🗡️", layout="wide")

# Backend URL (FastAPI runs on port 8000 in the api_backend container)
API_BASE_URL = "http://api_backend:8000"

# --- STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

if "db_populated" not in st.session_state:
    try:
        res = requests.get(f"{API_BASE_URL}/db-status")
        if res.status_code == 200:
            st.session_state.db_populated = res.json().get("has_documents", False)
        else:
            st.session_state.db_populated = False
    except Exception:
        st.session_state.db_populated = False

st.title("🗡️ Cloven Viscount - Document Intelligence")
st.markdown("Upload a PDF document and ask questions to the RAG model.")

if st.session_state.db_populated or st.session_state.file_processed:
    st.info("ℹ️ The database already contains documents. You can ask questions or upload a new PDF to enrich the knowledge base.")
else:
    st.warning("⚠️ Warning: Please make sure to upload and process a document before asking questions.")

# --- SIDEBAR: UPLOAD & DOCUMENT MANAGEMENT ---
with st.sidebar:
    st.header("1. Document Ingestion")
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Uploading document to server..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    # Expecting 202 Accepted from our asynchronous architecture
                    if response.status_code == 202:
                        data = response.json()
                        task_id = data.get('task_id')
                        doc_id = data.get('document_id')
                        
                        st.info(f"Task ID: {task_id} generated. Starting background processing...")
                        
                        status = "PENDING"
                        status_placeholder = st.empty() 
                        
                        while status not in ["SUCCESS", "FAILURE", "FAILED"]:
                            status_placeholder.info(f"⏳ Current status: {status}... extracting vectors.")
                            
                            status_response = requests.get(f"{API_BASE_URL}/document-status/{doc_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                # Updated to match backend JSON key
                                status = status_data.get("task_status")
                                msg = status_data.get("message", "Elaboration ongoing...")

                                if status not in ["SUCCESS", "FAILED"]:
                                    status_placeholder.info(f"⏳ {msg}")
                            else:
                                st.error("Error communicating with the backend status endpoint.")
                                break
                                
                            time.sleep(2) 
                        
                        status_placeholder.empty() 
                        if status == "SUCCESS":
                            st.success("✅ Document processed successfully! You can now ask questions.")
                            st.session_state.file_processed = True
                            # Save to session for deletion management
                            st.session_state.uploaded_docs[uploaded_file.name] = doc_id
                        elif status in ["FAILURE", "FAILED"]:
                            st.error("❌ There was an error processing the document by the worker.")
                            
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Backend connection error: {e}")

    st.divider()
    
    # --- HARD DELETE MANAGEMENT ---
    st.header("2. Manage Database")
    if not st.session_state.uploaded_docs:
        st.write("No documents processed in this session.")
    else:
        for doc_name, doc_uuid in list(st.session_state.uploaded_docs.items()):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📄 {doc_name}")
            with col2:
                if st.button("Del", key=f"del_{doc_uuid}", help="Permanently delete from DB"):
                    with st.spinner("Deleting..."):
                        del_res = requests.delete(f"{API_BASE_URL}/documents/{doc_uuid}")
                        if del_res.status_code == 200:
                            del st.session_state.uploaded_docs[doc_name]
                            st.rerun()
                        else:
                            st.error(f"Failed to delete: {del_res.text}")

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
                    st.error(f"Backend error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Backend connection error: {e}")