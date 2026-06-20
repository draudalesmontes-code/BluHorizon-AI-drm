from services.postgres.postgresDB import get_connection
from services.embedding import chunk_text, embed_batch, embed_text
import numpy as np
import psycopg2
import psycopg2.extras


def add_chunks(document_id: int, text: str) -> list[int]:
    chunk_of_text = chunk_text(text)
    vectors = embed_batch(chunk_of_text)
    ids = []
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # clear any existing chunks for this document so re-upload replaces, not appends
            cur.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
            for chunk, vector in zip(chunk_of_text,vectors):
                cur.execute(
                    "INSERT INTO chunks (document_id, chunk_text, embedding) "
                    "VALUES (%s,%s,%s) RETURNING id",
                    (document_id, chunk, np.array(vector))
                )
                ids.append(cur.fetchone()["id"])
    return ids


## embed the query and return the user's most similar chunks via cosine search
def query(query_text: str, n_results: int, user_id: int) -> list[dict]:
    query_vector = np.array(embed_text(query_text))
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT c.id, c.chunk_text, d.filename AS source, "
                "1 - (c.embedding <=> %s) AS score "
                "FROM chunks c "
                "JOIN documents d ON c.document_id = d.id "
                "WHERE d.user_id = %s "
                "ORDER BY c.embedding <=> %s "
                "LIMIT %s",
                (query_vector, user_id, query_vector, n_results)
            )
            return [
                {
                    "text": row["chunk_text"],
                    "id": row["id"],
                    "metadata": {"source": row["source"]},
                    "score": round(float(row["score"]), 4),
                }
                for row in cur.fetchall()
            ]


## count how many embedded chunks belong to a user (used to size the candidate pool)
def get_info(user_id: int) -> dict:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT COUNT(*) AS total_vectors FROM chunks c "
                "JOIN documents d ON c.document_id = d.id "
                "WHERE d.user_id = %s AND c.embedding IS NOT NULL",
                (user_id,)
            )
            row = cur.fetchone()
    return {"total_vectors": row["total_vectors"], "embedding_dim": 384}