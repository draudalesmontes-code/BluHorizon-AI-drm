from services.postgres.postgresDB import get_connection
import psycopg2
import psycopg2.extras
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

## hash password and insert new user, returns generated user id
def register_user(email: str, password: str) -> int:
    hashed = pwd_context.hash(password)
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s) RETURNING id",
                (email, hashed)
            )
            row = cur.fetchone()
            return row["id"]

## fetch a user row by email, returns None if not found
def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, email, password_hash, created_at FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            return dict(row) if row else None