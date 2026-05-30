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

st.title("🗡️ Cloven Viscount - Document Intelligence")
st.markdown("Upload a PDF document and ask questions to the RAG model.")

# --- SIDEBAR: UPLOAD MANAGEMENT ---
with st.sidebar:
    st.header("1. Document Ingestion")
    uploaded_file = st.file_uploader("Upload a PDF document", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Sending document to background worker..."):
                try:
                    # Call the FastAPI upload endpoint
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ File accepted! Processing in background.")
                        st.info(f"Task ID: {data.get('task_id')}")
                        st.session_state.file_processed = True
                        
                        # Short pause to let Celery handle the initial chunking
                        # In a future update, we will implement task status polling
                        time.sleep(2) 
                    else:
                        st.error(f"Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Backend connection error: {e}")

# --- MAIN AREA: CHAT INTERFACE ---
st.header("2. Document Query (Chat)")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Ask a question about the uploaded document..."):
    # Warning if the user hasn't uploaded a file yet
    if not st.session_state.file_processed:
        st.warning("⚠️ Warning: Please make sure to upload and process a document before asking questions.")

    # 1. Add user question to the UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call the backend API
    with st.chat_message("assistant"):
        with st.spinner("Searching documents and generating response..."):
            try:
                # Call our new /chat endpoint
                payload = {"query": prompt}
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