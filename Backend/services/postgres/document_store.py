from services.postgres.postgresDB import get_connection
import psycopg2
import psycopg2.extras

## insert a document row or update file_type if (user_id, filename) already exists
def upsert_document(user_id: int, filename: str, file_type: str) -> int:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO documents (user_id, filename, file_type) VALUES (%s, %s, %s) "
                "ON CONFLICT (user_id, filename) DO UPDATE SET file_type = EXCLUDED.file_type "
                "RETURNING id",
                (user_id, filename, file_type)
            )
            row = cur.fetchone()
            return row["id"]

## fetch all documents belonging to a user ordered by most recently uploaded
def list_documents(user_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, filename, file_type, uploaded_at FROM documents WHERE user_id = %s ORDER BY uploaded_at DESC",
                (user_id,)
            )
            return [dict(row) for row in cur.fetchall()]