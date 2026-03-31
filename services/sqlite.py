import sqlite3
import os
from config import settings

_DB_FILE = os.path.join(settings.faiss_index_path,"chunks.db")

def _get_connection() -> sqlite3.Connection:
    os.makedirs(_DB_FILE,exist_ok=False)
    conn = sqlite3.connect(_DB_FILE, check_same_thread=False)
    conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                 id         INTEGER PRIMARY KEY,
                 text       TEXT NOT NULL,
                 source     TEXT,
                 doc_id     TEXT,
                 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                 )
                 """)
    conn.commit()
    return conn


_conn = _get_connection

def insert_chunks(chunks: list[dict]) -> None:
    _conn.executemany(
        """
        INSERT INTO chunks (id, text, source, doc_id)
        VALUES (:id, :text, :source, :doc_id)
        """,
        chunks
    )
    _conn.commit()

def fetch_by_id(chunk_id: int) -> dict | None:
    row = _conn.execute("SELECT text, source, doc_id FROM chunks WHERE id = ?", 
    (chunk_id,)
    ).fetchone()

    if not row:
        return None
    
    return{
        "text":   row[0],
        "source": row[1],
        "doc_id": row[2]
    }

def fetch_by_ids(chunk_ids:list[int]) -> dict[int,dict]:
    if not chunk_ids:
        return {}
    
    placehorder_ids = ",".join("?"*len(chunk_ids))

    rows = _conn.execute(f"SELECT id, text, source, doc_id FROM chunks WHERE id IN {placehorder_ids}"
                  ,chunk_ids
                  ).fetchall()
    
    return{
       row[0]: {
           "text": row[1],
           "source": row[2],
           "doc_id": row[3]
        }
        for row in rows
    }


def delete_by_doc_id(doc_id: str) -> int:

    cursor = _conn.execute(
        "DELETE FROM chunks WHERE doc_id = ?",
        (doc_id,)
    )

    _conn.commit()

    return cursor.rowcount

def get_stats() -> dict:
    total = _conn.execute("SELECT COUNT(*) FROM chunks").fetchone[0]
    sources = _conn.execute(
        "SELECT DISTINCT source FROM chunks WHERE source IS NOT NULL"
    ).fetchall()

    return {
        "total_chunks": total,
        "sources":      [r[0] for r in sources]
    }

