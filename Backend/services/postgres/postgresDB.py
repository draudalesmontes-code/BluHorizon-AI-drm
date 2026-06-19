import psycopg2
import psycopg2.extras
from config import settings


def get_connection():
    conn = psycopg2.connect(settings.database_url)
    return conn


def get_cursor(conn):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return cursor
