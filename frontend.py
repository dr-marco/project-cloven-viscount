import streamlit as st
import requests

API_URL = "http://api_backend:8000"

st.set_page_config(page_title="Cloven Viscount", page_icon="🗡️")
st.title("Project Cloven Viscount 🗡️")
st.markdown("Your RAG-powered document assistant.")

# --- SIDEBAR: Upload Documenti ---
with st.sidebar:
    st.header("Document Ingestion")
    uploaded_file = st.file_uploader("Upload a new PDF", type=["pdf"])
    
    if st.button("Process Document") and uploaded_file:
        with st.spinner("Chunking and vectorizing..."):
            # Prepariamo il file per essere inviato via POST
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            try:
                response = requests.post(f"{API_URL}/upload", files=files)
                if response.status_code == 200:
                    st.success(f"Successfully ingested: {uploaded_file.name}")
                else:
                    st.error(f"API Error: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the Backend API. Is it running?")

# --- MAIN AREA: Interfaccia Chat ---
st.header("Query your documents")

# Inizializza lo storico della chat nella sessione
if "messages" not in st.session_state:
    st.session_state.messages = []

# Disegna i messaggi passati
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input testuale per la nuova domanda
if prompt := st.chat_input("Ask something about the ingested documents..."):
    # 1. Mostra la domanda dell'utente
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Chiama l'API per ottenere la risposta
    with st.chat_message("assistant"):
        with st.spinner("Searching the vector space..."):
            try:
                response = requests.post(f"{API_URL}/analyze", json={"question": prompt})
                if response.status_code == 200:
                    answer = response.json().get("answer", "No answer generated.")
                    st.markdown(answer)
                    # Salva la risposta nello storico
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"API Error: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the Backend API.")