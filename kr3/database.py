import sqlite3
from contextlib import contextmanager

DATABASE_NAME = "users.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        conn.commit()
        print("Database initialized successfully")

@contextmanager
def get_db_cursor():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()

def create_user(username: str, password: str) -> int:
    with get_db_cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        return cursor.lastrowid

def get_user_by_username(username: str):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, username, password FROM users WHERE username = ?",
            (username,)
        )
        return cursor.fetchone()

def get_all_users():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, username, password FROM users")
        return cursor.fetchall()

def delete_user(user_id: int):
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount

if __name__ == "__main__":
    init_db()
