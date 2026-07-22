# BluHorizon AI — Full-Stack RAG Application

## Overview

BluHorizon AI is a full-stack Retrieval-Augmented Generation (RAG) system with a Flutter mobile frontend and a Python FastAPI backend. Users can ingest documents (PDF, DOCX, XLSX), which are embedded into a FAISS vector store and queried through an AI-powered chat interface backed by Claude.

## Tech Stack

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
│       ├── rag_pipeline.py        ← HyDE-based RAG pipeline
│       ├── embedding.py           ← Vector embedding generation
│       ├── store_faiss_vector.py  ← FAISS vector store operations
│       └── sqlite.py              ← SQLite integration
└── Frontend (port 3000)
    └── Flutter mobile app
```

## Branches

This repository currently has two important branches:

| Branch | Purpose | Notes |
|--------|---------|-------|
| `main` | Stable baseline for the current full-stack RAG application | Uses the existing FAISS-based retrieval flow with SQLite/Firebase-era persistence pieces. This is the branch to use when reviewing the original working demo. |
| `postgres-migration` | Work-in-progress migration toward a production-style Postgres backend | Adds Postgres schema and migration files, seeded SQL data, JWT/auth support, a Flutter login screen, and updated API wiring. This branch is for testing the database/auth refactor before merging it back into `main`. |

### Branch Workflow

- Use `main` for the current stable demo and portfolio review.
- Use `postgres-migration` when working on the database migration, login flow, JWT handling, or Postgres-backed document/vector storage.
- Keep feature work on the migration branch until the backend, frontend login flow, Docker setup, and tests are confirmed together.
- Merge `postgres-migration` into `main` only after the app can run cleanly with Postgres through Docker Compose.

## Key Features

- **HyDE RAG Pipeline** — generates a hypothetical answer to the user query, embeds it, and uses it for semantic retrieval — improving recall over naive keyword search
- **Gap-aware chunk filtering** — dynamic score-gap cutoff selects the most relevant document chunks rather than a fixed top-K
- **Document ingestion** — supports PDF, DOCX, and XLSX with configurable chunking
- **Tool-augmented Claude** — web search and code execution tools extend Claude within the chat interface
- **Containerized deployment** — single `docker-compose up` launches the full stack

## RAG Pipeline Flow

```
User query
  → HyDE: Claude generates hypothetical document
  → Embed hypothetical doc with Sentence-Transformers
  → FAISS similarity search
  → Gap-aware chunk selection
  → Retrieved chunks + original query → Claude response
```

## Getting Started

```bash
docker-compose up --build
```

Set the following environment variables before running:

```
ANTHROPIC_API_KEY=...
TAVILY_API_KEY=...
```

The backend will be available at `http://localhost:8000` and the Flutter web frontend at `http://localhost:3000`.
