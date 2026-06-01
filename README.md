# 📚 Project Cloven Viscount - Enterprise RAG Architecture

Cloven Viscount is a production-ready, asynchronous Retrieval-Augmented Generation (RAG) system built to converse with corporate documents. Designed with separation of concerns in mind, it decouples heavy document ingestion from fast LLM querying, ensuring a highly responsive User Experience.

> ⚠️ **DISCLAIMER: Proof of Concept / Playground Environment**
> This repository (*Project Cloven Viscount*) has evolved to include core security and operational patterns (such as IP-based rate limiting and input sanitization). However, it remains an architectural Proof of Concept (PoC) built for personal exploration. It deliberately omits production-grade safeguards like robust User Authentication (OAuth2/OIDC), TLS termination at the application level, and a persistent, scalable relational database layer. **Do not deploy this code directly to a public-facing production environment "as is".**

## 🏗️ Architecture & Tech Stack

- **Gateway & API:** FastAPI (with lifespan cold-start optimization)
- **Frontend:** Streamlit (Async Polling & Dynamic Status)
- **Background Workers:** Celery + Redis (Message Broker)
- **Vector Database:** ChromaDB (Persistent local volume)
- **LLM Engine:** LangChain (Pure LCEL implementation) + Groq (LLaMA-3)
- **Security:** `slowapi` for Rate Limiting & DoS prevention
- **Infrastructure:** Docker Compose (with Hot Reload for development)

## ✨ Core Features

1. **Asynchronous Document Ingestion:** Uploaded PDFs are handed off to background Celery workers. The UI polls the backend via a dedicated status endpoint, preventing timeout errors on large documents.
2. **History-Aware Conversational Memory:** The system doesn't just search; it remembers. Using a dual-pass LCEL chain, the LLM reformulates user queries based on past chat history before querying the vector store, allowing for natural use of pronouns and contextual follow-ups.
3. **Basic security:** API endpoints are protected against path traversal and shielded by an IP-based rate limiter (max 5 requests/minute) to prevent API key depletion.
4. **Optimized Cold Start:** HuggingFace embedding models and ChromaDB instances are pre-warmed during FastAPI's boot sequence, ensuring the user's first query is instantly processed.

## 🚀 Getting Started (Development)

1. Clone the repository.
2. Ensure you have your `.env` file configured with your `GROQ_API_KEY`.
3. Create a `docker-compose.override.yml` for local Hot Reload (added to `.gitignore`):
   ```yaml
   version: '3.8'
   services:
     api_backend:
       volumes:
         - .:/app
       command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

4. Build and run the infrastructure:
```bash
docker-compose up -d

```

5. Access the Streamlit UI at `http://localhost:8501`.

## 🛣️ Roadmap - next phase

* Phase D: Relational Database (PostgreSQL) for Document/User Metadata & Deletion logic.
