import sqlite3
from contextlib import contextmanager
from typing import List, Optional

DATABASE_NAME = "todos.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_todo_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        print("Todo database initialized successfully")

@contextmanager
def get_todo_cursor():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()

def create_todo(title: str, description: str) -> int:
    with get_todo_cursor() as cursor:
        cursor.execute(
            "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
            (title, description)
        )
        return cursor.lastrowid

def get_todo(todo_id: int) -> Optional[dict]:
    with get_todo_cursor() as cursor:
        cursor.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (todo_id,)
        )
        return cursor.fetchone()

def get_all_todos() -> List[dict]:
    with get_todo_cursor() as cursor:
        cursor.execute("SELECT id, title, description, completed FROM todos")
        return cursor.fetchall()

def update_todo(todo_id: int, title: str, description: str, completed: bool) -> bool:
    with get_todo_cursor() as cursor:
        completed_int = 1 if completed else 0
        cursor.execute(
            """UPDATE todos 
               SET title = ?, description = ?, completed = ? 
               WHERE id = ?""",
            (title, description, completed_int, todo_id)
        )
        return cursor.rowcount > 0

def delete_todo(todo_id: int) -> bool:
    with get_todo_cursor() as cursor:
        cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        return cursor.rowcount > 0

if __name__ == "__main__":
    init_todo_db()
