import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from config import settings


def get_connection():
    conn = psycopg2.connect(settings.database_url)
    register_vector(conn)
    return conn


def get_cursor(conn):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cursor
