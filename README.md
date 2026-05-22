# project-cloven-viscount

An API-first Retrieval-Augmented Generation (RAG) system designed to analyze and query unstructured documents using Large Language Models (LLMs).

> ⚠️ **DISCLAIMER: Proof of Concept / Playground Environment**
> This repository (*Project Cloven Viscount*) is an architectural Proof of Concept (PoC) built for personal exploration of modern AI/ML engineering patterns. It deliberately omits critical production safeguards (e.g., input sanitization, authentication, rate limiting, production-grade WSGI servers) to keep the codebase minimal. **Do not deploy this code to a public-facing environment "as is".**

## Architecture Overview

This project implements a containerized RAG pipeline focusing on backend robustness and dynamic data ingestion.

*   **API Framework:** FastAPI (Python 3.10)
*   **Orchestration:** Docker & Docker Compose
*   **Vector Store:** ChromaDB (Persistent local storage)
*   **Embeddings:** `all-MiniLM-L6-v2` via HuggingFace (Local CPU inference)
*   **LLM Inference:** Llama-3 via Groq API (Cloud inference)
*   **Pipeline Logic:** LangChain Core (LCEL syntax)

## System Flow

1.  **Ingestion:** PDF documents are parsed and chunked using LangChain's `RecursiveCharacterTextSplitter`.
2.  **Vectorization:** Text chunks are converted into 384-dimensional embeddings and stored in a persistent ChromaDB volume.
3.  **Retrieval:** User queries are matched against the vector database using Cosine Similarity (HNSW graph).
4.  **Generation:** The top-k relevant chunks are passed as context to the LLM via LangChain Expression Language (LCEL) pipelines to generate deterministic, fact-grounded responses.

## Setup & Installation

### Prerequisites
*   Docker and Docker Compose installed.
*   A valid Groq API Key.

### Initialization

1. Clone the repository:
   
```bash
   git clone <your-repo-url>
   cd cv-analyzer
```
2. Configure environment variables:
Create a `.env` file in the root directory:

```env
   GROQ_API_KEY=gsk_your_api_key_here

```

3. Build and run the infrastructure:

```bash
   docker-compose up --build

```

## API Documentation

Once the container is running, the interactive Swagger UI is available at:
`http://localhost:8000/docs`

### Core Endpoints

* `GET /`: Health check.
* `POST /analyze`: Accepts a JSON payload with a `question` string. Queries the Vector DB and returns the LLM-generated response.
* *(Planned)* `POST /upload`: Dynamic ingestion of new PDF documents into the running Vector DB.

## Data Persistence

The ChromaDB vector store is mapped to a local Docker Volume (`./chroma_data`). This ensures that embeddings are preserved across container restarts. Do not commit this directory to version control.