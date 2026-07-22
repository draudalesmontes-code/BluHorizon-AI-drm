# BluHorizon AI — Full-Stack RAG Application

## Overview

BluHorizon AI is a full-stack Retrieval-Augmented Generation (RAG) system with a Flutter mobile frontend and a Python FastAPI backend. Users can ingest documents (PDF, DOCX, XLSX), which are embedded into a FAISS vector store, then query them through an AI-powered chat interface backed by Claude.

## Technologies

| Layer | Stack |
|-------|-------|
| Frontend | Flutter (Dart), mobile-first |
| Backend | Python, FastAPI, Uvicorn |
| AI | Anthropic Claude API |
| Vector DB | FAISS (CPU) |
| Embeddings | Sentence-Transformers |
| Database | Firebase, SQLite |
| ML | PyTorch, tiktoken |
| Search | Tavily API |
| Deployment | Docker, Docker Compose |

## Architecture

```
docker-compose.yml
├── Backend (port 8000)
│   ├── routers/         ← chat, RAG, agents endpoints
│   └── services/
│       ├── claude_client.py       ← Anthropic API wrapper (tool support)
│       ├── rag_pipeline.py        ← HyDE-based RAG pipeline
│       ├── embedding.py           ← Vector embedding generation
│       ├── store_faiss_vector.py  ← FAISS vector store operations
│       └── sqlite.py              ← SQLite integration
└── Frontend (port 3000)
    └── Flutter mobile app
        └── ViewModels (GPS, Camera)
```

## Key Features

- **HyDE RAG Pipeline**: Generates a hypothetical answer to the user query, embeds it, and uses it for semantic retrieval — improving recall over naive keyword search
- **Gap-aware chunk filtering**: Dynamic score-gap cutoff selects the most relevant document chunks rather than using a fixed top-K
- **Document ingestion**: Supports PDF, DOCX, and XLSX with configurable chunking strategies
- **Tool-augmented Claude**: Custom tools (web search, code execution) extend Claude's capabilities within the chat interface
- **Mobile-native features**: GPS and camera ViewModels integrated into the Flutter frontend
- **Containerized deployment**: Single `docker-compose up` launches both backend and frontend

## Team Contributions

- **Diego**: ViewModels (GPS and Camera integration)
- **Payton**: UI/UX design
- **Jacky + Connor**: Firebase / database layer

## RAG Pipeline Flow

```
User query
  → HyDE: Claude generates hypothetical document
  → Embed hypothetical doc with Sentence-Transformers
  → FAISS similarity search
  → Gap-aware chunk selection
  → Retrieved chunks + original query → Claude response
```
