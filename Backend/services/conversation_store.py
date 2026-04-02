from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Optional


def _data_dir() -> Path:
    docker_dir = Path("/app/faiss_data")
    if docker_dir.exists():
        docker_dir.mkdir(parents=True, exist_ok=True)
        return docker_dir

    local_dir = Path(__file__).resolve().parents[1] / "faiss_data"
    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir


DB_PATH = _data_dir() / "app_state.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                session_id   TEXT PRIMARY KEY,
                title        TEXT,
                created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id   TEXT NOT NULL,
                role         TEXT NOT NULL,
                content      TEXT NOT NULL,
                created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES conversations(session_id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages(session_id, id);

            CREATE TABLE IF NOT EXISTS documents (
                doc_id       TEXT PRIMARY KEY,
                filename     TEXT NOT NULL,
                source       TEXT NOT NULL,
                file_type    TEXT NOT NULL,
                uploaded_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def create_session(title: Optional[str] = None) -> str:
    session_id = str(uuid.uuid4())
    with _conn() as conn:
        conn.execute(
            "INSERT INTO conversations (session_id, title) VALUES (?, ?)",
            (session_id, title),
        )
    return session_id


def ensure_session(session_id: str, title: Optional[str] = None) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO conversations (session_id, title)
            VALUES (?, ?)
            ON CONFLICT(session_id) DO NOTHING
            """,
            (session_id, title),
        )


def append_message(session_id: str, role: str, content: str) -> None:
    ensure_session(session_id)

    with _conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,),
        )


def get_history(session_id: str) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    return [{"role": row["role"], "content": row["content"]} for row in rows]


def list_sessions(limit: int = 50) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def clear_session(session_id: str) -> None:
    with _conn() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM conversations WHERE session_id = ?", (session_id,))


def upsert_document(doc_id: str, filename: str, source: str, file_type: str) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO documents (doc_id, filename, source, file_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
                filename = excluded.filename,
                source = excluded.source,
                file_type = excluded.file_type,
                uploaded_at = CURRENT_TIMESTAMP
            """,
            (doc_id, filename, source, file_type),
        )


def list_documents() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            """
            SELECT doc_id, filename, source, file_type, uploaded_at
            FROM documents
            ORDER BY uploaded_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]
