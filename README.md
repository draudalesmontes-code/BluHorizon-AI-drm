# BluHorizon AI

Full-stack agentic RAG application with a Flutter frontend, a Python FastAPI backend, Claude-powered chat, Tavily web search, Postgres/pgvector retrieval, and JWT-backed user accounts.

## What It Does

BluHorizon AI lets users register, log in, upload documents, index them into a user-scoped Postgres vector store, and chat with an agent that can combine Claude responses with document search, web search, and limited Python execution. The app is packaged with Docker Compose so the Postgres database, API, and Flutter web UI can run together.

## Main Branch Stack

| Layer | Technology |
| --- | --- |
| Frontend | Flutter, Dart, Material 3, login screen, `http`, `flutter_markdown`, `google_fonts`, `file_picker`, `shared_preferences`, `uuid` |
| Backend API | Python 3.11, FastAPI, Uvicorn, Pydantic, pydantic-settings |
| Auth | JWT bearer auth, `python-jose`, `passlib[bcrypt]`, `bcrypt`, `email-validator` |
| LLM | Anthropic Claude via `anthropic` SDK |
| Agent Tools | Tavily web search, restricted Python execution, RAG document search |
| RAG | HyDE query expansion, Sentence Transformers embeddings, pgvector similarity search, score-gap chunk filtering |
| Embeddings | `sentence-transformers` with `all-MiniLM-L6-v2` 384-dimensional vectors |
| Storage | PostgreSQL 16 with pgvector for users, documents, chunks, embeddings, conversations, and messages |
| File Ingestion | Plain text/code/data files, PDF via `pypdf`, DOCX via `python-docx`, XLSX via `openpyxl` |
| Deployment | Docker, Docker Compose, `pgvector/pgvector:pg16`, Nginx for the Flutter web build |
| Tests | `pytest` service/evaluation tests and Flutter widget test scaffold |

## Branches

The README describes the current `main` branch, which is the Postgres-backed stack. In older checkouts, the same Postgres work may still appear as `postgres-migration`; treat that branch as the migration/pre-merge version of the current architecture.

| Branch | Purpose | Stack Notes |
| --- | --- | --- |
| `main` | Current full-stack RAG app | Flutter frontend, FastAPI backend, Claude/Tavily tools, Postgres/pgvector retrieval, JWT auth, password hashing, SQL migrations, and user-scoped data. |
| `postgres-migration` | Historical migration branch, if present | Contains the Postgres migration work before it is treated as main: pgvector Docker DB, schema/migrations, Postgres stores, auth, login UI, and RAG evaluation tests. |

If an older clone still has the Postgres implementation only on the migration branch, switch to it with:

```bash
git fetch origin
git switch --track origin/postgres-migration
```

Once that work is merged or fast-forwarded into `main`, use `main` as the source of truth.

The Postgres stack starts a `db` service, initializes SQL files from `Backend/database/`, and maps the Flutter web frontend to `http://localhost:3001`.

## Main Branch Runtime Architecture

`docker-compose.yml` is the main way to run the full stack.

```text
docker-compose.yml
|-- db: PostgreSQL 16 + pgvector on localhost:5432
|   |-- Backend/database/blu_schema.sql
|   `-- Backend/database/migrations/*.sql
|-- api: FastAPI on http://localhost:8000
|   |-- Dockerfile.api
|   `-- Backend/
|       |-- dependencies.py  # JWT bearer-token user dependency
|       |-- main.py
|       |-- routers/
|       |   |-- auth.py      # register/login endpoints
|       |   |-- chat.py      # direct Claude chat and chat history
|       |   |-- rag.py       # document upload, ingest, query, prompt generation, stats
|       |   `-- agents.py    # Claude tool-use agent loop
|       |-- services/
|       |   |-- claude_client.py
|       |   |-- embedding.py
|       |   |-- file_ingest.py
|       |   |-- jwt.py
|       |   |-- rag_pipeline.py
|       |   |-- postgres/
|       |   |   |-- auth_store.py
|       |   |   |-- document_store.py
|       |   |   |-- postgresDB.py
|       |   |   |-- postgres_store.py
|       |   |   `-- vector_store.py
|       |   `-- legacy/       # older SQLite/FAISS implementation, kept for reference
|       `-- tools/
|           |-- code_tool.py
|           |-- rag_tool.py
|           `-- search_tool.py
`-- frontend: Flutter web app served by Nginx on http://localhost:3001
    |-- frontend/Dockerfile
    `-- frontend/lib/
        |-- screens/login_screen.dart
        |-- screens/chat_screen.dart
        |-- screens/documents_drawer.dart
        |-- services/auth_store.dart
        |-- services/api_service.dart
        `-- models/message.dart
```

The Docker Compose API service copies and runs the `Backend/` directory. `Dockerfile.api` and `frontend/Dockerfile` are the active Dockerfiles for the composed stack. The top-level `Dockerfile` and `Dockerfile.flutter` are alternate or legacy build files.

## Data Flow

```text
Register/login
  -> password hash stored in Postgres
  -> JWT access token returned to Flutter
  -> protected API requests include Authorization: Bearer <token>

Document upload or text ingest
  -> authenticated user id from JWT
  -> file/text extraction
  -> token chunking with overlap
  -> Sentence Transformers embeddings
  -> document row in Postgres
  -> chunk text + vector(384) embedding in Postgres/pgvector

User question
  -> authenticated user id from JWT
  -> Claude generates a HyDE hypothetical answer
  -> HyDE answer is embedded
  -> pgvector similarity search retrieves candidate chunks for that user
  -> score-gap filtering chooses the strongest chunks
  -> Claude answers using the retrieved context
```

Agent chat uses the same document search path as a tool and can also call Tavily web search or the restricted Python tool when those toggles are enabled in the Flutter UI.

## Persistence

Runtime data is stored in Postgres. The Docker Compose `postgres_data` volume persists the database across container restarts.

| Table | Purpose |
| --- | --- |
| `users` | Registered accounts and password hashes |
| `documents` | User-owned uploaded document records |
| `chunks` | Parsed text chunks and `vector(384)` embeddings |
| `conversations` | User-owned chat sessions |
| `messages` | Conversation message history |

The compose file may still mount `./Backend/faiss_data` for compatibility with older code paths, but the active RAG path stores and searches embeddings through Postgres/pgvector.

## API Surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Health check |
| `POST` | `/auth/register` | Create a user account |
| `POST` | `/auth/login` | Return a JWT bearer token |
| `POST` | `/chat/` | Direct Claude chat with optional persisted conversation history |
| `GET` | `/chat/history/{conversation_id}` | Fetch messages for one conversation |
| `GET` | `/chat/sessions` | List recent conversations for the current user |
| `DELETE` | `/chat/history/{conversation_id}` | Delete one conversation |
| `GET` | `/chat/models` | Return the configured Claude model |
| `POST` | `/rag/ingest` | Index raw text for the current user |
| `POST` | `/rag/upload` | Upload and index a supported file |
| `GET` | `/rag/documents` | List current user's uploaded/indexed documents |
| `POST` | `/rag/query` | Ask a question against current user's indexed documents |
| `GET` | `/rag/stats` | Return current user's vector stats |
| `POST` | `/rag/generate-prompt` | Generate a reusable system prompt for a use case |
| `POST` | `/agents/run` | Run the Claude tool-use agent loop |
| `GET` | `/agents/tools` | List available agent tools |

Except for `/` and `/auth/*`, application endpoints require an `Authorization: Bearer <token>` header.

## Environment Variables

Create a `.env` file at the project root before running the backend or Docker Compose.

```env
ANTHROPIC_API_KEY=your_anthropic_key
TAVILY_API_KEY=your_tavily_key
DATABASE_URL=postgresql://postgres:your_password@db:5432/bluhorizon
SECRET_KEY=replace_with_a_long_random_secret

# Optional defaults from Backend/config.py
CLAUDE_MODEL=claude-haiku-4-5
MAX_TOKENS=4096
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

`ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, `DATABASE_URL`, and `SECRET_KEY` are required because the settings object loads them without fallback values. When running the backend directly on your machine instead of inside Docker Compose, use `localhost` in `DATABASE_URL` instead of `db`.

## Run With Docker Compose

```bash
docker-compose up --build
```

Then open:

- Frontend: `http://localhost:3001`
- Backend health check: `http://localhost:8000/`
- FastAPI docs: `http://localhost:8000/docs`
- Postgres: `localhost:5432`

## Run Locally

Backend:

```bash
docker compose up db
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
flutter pub get
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

For Android emulator builds, the frontend falls back to `http://10.0.2.2:8000` when `API_BASE_URL` is not provided. For web builds, it falls back to `http://localhost:8000`.

## Supported Upload Types

The backend accepts:

- Text-like files: `.txt`, `.md`, `.json`, `.py`, `.java`, `.csv`, `.yaml`, `.yml`, `.xml`
- Documents: `.pdf`, `.docx`, `.xlsx`

The Flutter document picker currently exposes `.txt`, `.md`, `.json`, `.py`, `.java`, `.csv`, `.pdf`, `.docx`, and `.xlsx`.

## Tests

Backend service tests:

```bash
cd Backend
python -m pytest tests/services_unit_test.py -v
```

RAG evaluator tests without live LLM calls:

```bash
cd Backend
python -m pytest tests/rag_eval_test.py -v -m "not llm_eval"
```

Live RAG quality evaluations against Postgres and Claude:

```bash
cd Backend
RUN_LLM_EVALS=1 python -m pytest tests/rag_eval_test.py -v -m llm_eval
```

Manual API smoke test:

```bash
cd Backend
uvicorn main:app --reload
python test_all.py
```

Note: `Backend/test_all.py` is intended as a manual smoke script and should be checked before use because its agent examples may need the `/agents/...` prefix used by the actual FastAPI router.

Flutter tests:

```bash
cd frontend
flutter test
```

## Key Implementation Notes

- The chat screen sends messages through `/agents/run`, not the simpler `/chat/` endpoint, so the UI can expose web search, code, and RAG toggles.
- The Flutter frontend stores the JWT locally and attaches it as a bearer token for protected API calls.
- Uploaded files are parsed in memory, chunked with `tiktoken`, embedded with Sentence Transformers, and stored in Postgres.
- pgvector stores 384-dimensional embeddings and supports user-scoped similarity search across uploaded document chunks.
- RAG retrieval uses a floor score, minimum chunk count, maximum chunk count, and largest score-gap cutoff instead of a fixed top-K response.
- The Python execution tool uses a deliberately small builtins allowlist and is meant for calculations or simple transformations, not arbitrary system access.
- `.env`, `faiss_data/`, `venv/`, and Python cache files are ignored by Git.
