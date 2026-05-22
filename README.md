# project-cloven-viscount

An API-first Retrieval-Augmented Generation (RAG) system with a decoupled UI, designed to dynamically ingest and query unstructured documents using Large Language Models (LLMs).

> ⚠️ **DISCLAIMER: Proof of Concept / Playground Environment**
> This repository (*Project Cloven Viscount*) is an architectural Proof of Concept (PoC) built for personal exploration of modern AI/ML engineering patterns. It deliberately omits critical production safeguards (e.g., input sanitization, authentication, rate limiting, production-grade WSGI servers) to keep the codebase minimal. **Do not deploy this code to a public-facing environment "as is".**

## Architecture Overview

The system follows a microservices architecture orchestrated via Docker Compose, separating the ingestion/generation logic from the user interface:

*   **Backend API:** FastAPI (Python 3.10) exposing REST endpoints.
*   **Frontend UI:** Streamlit container communicating internally with the API.
*   **Vector Store:** ChromaDB (Persistent local Docker Volume).
*   **Embeddings:** `all-MiniLM-L6-v2` via HuggingFace (Local CPU inference).
*   **LLM Inference:** Llama-3 via Groq API (Cloud inference).
*   **Pipeline Logic:** LangChain Core (LCEL syntax).

## System Flow

1.  **Dynamic Ingestion:** Users upload PDF documents via the UI or API. The backend parses and chunks the text using `RecursiveCharacterTextSplitter`.
2.  **Vectorization:** Chunks are converted into 384-dimensional embeddings and stored in the persistent ChromaDB volume (`./chroma_data`) in real-time.
3.  **Retrieval:** User queries are matched against the vector database using Cosine Similarity (HNSW graph algorithm).
4.  **Generation:** The top-k relevant chunks are passed as context to the LLM via LangChain Expression Language (LCEL) to generate deterministic, fact-grounded responses.

## Setup & Run

### Prerequisites
*   Docker and Docker Compose installed.
*   A valid Groq API Key.

### Initialization

1. Clone the repository and configure the environment:
   
```bash
   git clone <your-repo-url>
   cd cv-analyzer
   
   # Create a .env file and add your API key
   echo "GROQ_API_KEY=gsk_your_api_key_here" > .env

```

2. Build and launch the cluster:

```bash
   docker-compose up --build

```

## System Interfaces

Once the containers are running, the system exposes two primary interfaces:

### 1. Frontend Interface (Streamlit)

* **URL:** `http://localhost:8501`
* **Usage:** Provides a graphical interface to upload PDF documents dynamically via the sidebar and chat with the vector database using the main chat window.

### 2. Backend API Docs (Swagger UI)

* **URL:** `http://localhost:8000/docs`
* **Endpoints:**
* `GET /`: System health check.
* `POST /upload`: Accepts `multipart/form-data` (PDF files), chunks the text, computes embeddings, and persists them to ChromaDB.
* `POST /analyze`: Accepts a JSON payload (`{"question": "..."}`), performs semantic search, and streams the context to the LLM to return the generated response.
