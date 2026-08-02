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
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, TAVILY_API_KEY if needed, and SECRET_KEY.
docker compose up --build
```

The Docker image uses Python 3.11 and installs the pinned Python dependencies
from `requirements.txt`. `docker-compose.yml` also provides safe placeholder
defaults so a fresh pull can build and boot before real API tokens are added.
The Compose Postgres database is exposed on host port `55432` to avoid
conflicts with a local macOS Postgres on `5432`.

Set the following environment variables in `.env` before running live AI
features:

```
ANTHROPIC_API_KEY=...
TAVILY_API_KEY=...
SECRET_KEY=...
POSTGRES_PASSWORD=local_dev_password
```

The backend will be available at `http://localhost:8000` and the Flutter web frontend at `http://localhost:3001`.

## Test suite

From `Backend/`, run the grouped backend suite with visible area headers and
RAG metric output:

```bash
python3 run_test_suite.py
```

Current active backend pytest coverage is 49 collected cases in `Backend/tests`:
36 service tests and 13 RAG eval tests. The RAG eval total is 5 free harness
checks plus 8 live quality checks, covering 4 eval cases across HyDE and
raw-question retrieval. `Backend/test_all.py` also contains 11 older manual
smoke checks, but it is not part of the master runner.

For local macOS runs, use Python 3.12 and install the eval/test dependencies
without legacy FAISS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.eval.txt
cd Backend
python run_test_suite.py --include-live
```

That master suite calls the service unit tests and the free RAG eval harness.
It skips paid/live Claude and Postgres-backed checks by default.
Legacy FAISS tests are skipped automatically if `faiss` is not installed.

To include the live checks, start Postgres, configure your environment, and opt
in explicitly:

```bash
python3 run_test_suite.py --include-live
```

You can run the same suite inside Docker after the image is built:

```bash
docker compose run --rm api python run_test_suite.py
docker compose run --rm api python run_test_suite.py --include-live
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
