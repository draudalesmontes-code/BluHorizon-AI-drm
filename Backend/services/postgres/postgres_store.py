from typing import Optional
from services.postgres.postgresDB import get_connection
import psycopg2
import psycopg2.extras

##create a conversation into conversation table in postgres sql
def create_conversation(user_id: int, title: Optional[str] = None) -> int:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id",
                (user_id, title)
            )
            row = cur.fetchone()
    return row["id"]

## append a new message row to messages table for a given conversation
def append_message(conversation_id: int, role: str,content: str)-> None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)"
            ,(conversation_id,role,content))

## fetch all messages for a conversation ordered oldest to newest
def get_history(conversation_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT role, content FROM messages WHERE conversation_id=%s ORDER BY id ASC",
            (conversation_id,))
            return [{"role": row["role"], "content": row["content"]} for row in cur.fetchall()]

## fetches n conversations from conversation table based on input
def list_conversations(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT %s",
            (limit,))
            return [dict(row) for row in cur.fetchall()]

## delete a conversation and cascade-delete all its messages
def clear_conversation(conversation_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("DELETE FROM conversations WHERE id=%s",
            (conversation_id,))

def upsert_document()