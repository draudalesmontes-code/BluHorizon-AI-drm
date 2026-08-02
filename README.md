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

## Test suite

From `Backend/`, run the grouped backend suite with visible area headers and
RAG metric output:

```bash
python3 run_test_suite.py
```

That master suite calls the service unit tests and the free RAG eval harness.
It skips paid/live Claude and Postgres-backed checks by default.
Legacy FAISS tests are skipped automatically if `faiss` is not installed.

To include the live checks, start Postgres, configure your environment, and opt
in explicitly:

```bash
python3 run_test_suite.py --include-live
```

The live RAG quality suite runs every eval case twice: once with HyDE retrieval
and once with raw-question retrieval. Its metric output includes deterministic
answer accuracy gates, LLM judge scores, chunks/sources used, and speed timings
for HyDE generation, retrieval, answer generation, and total RAG time.

## LLM evaluations

From `Backend/`, run the free evaluator/harness tests with:

```bash
SHOW_RAG_METRICS=1 python3 -m pytest tests/rag_eval_test.py -v -s -m "not llm_eval"
```

To run the end-to-end RAG quality cases against Postgres and Claude (uses API
tokens), start the database, configure `.env`, and opt in explicitly:

```bash
RUN_LLM_EVALS=1 SHOW_RAG_METRICS=1 python3 -m pytest tests/rag_eval_test.py -v -s -m llm_eval
```

Evaluation cases live in `Backend/tests/eval_cases.json`; add cases there to
expand the benchmark without changing the runner.
