"""Todo database — connection, schema, and display constants."""

import sqlite3

from shared import db_path

DB_PATH = db_path("tabs", "todos", "todos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'todo',
            due_date TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        )
    """)
    conn.commit()
    conn.close()


PRIORITY_COLORS = {0: "green", 1: "yellow", 2: "red"}
PRIORITY_LABELS = {0: "Low", 1: "Medium", 2: "High"}
STATUS_ICONS = {"todo": "☐", "in_progress": "◐", "done": "☑"}
STATUS_CYCLE = {"todo": "in_progress", "in_progress": "done", "done": "todo"}
