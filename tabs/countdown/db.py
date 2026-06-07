"""SQLite persistence for Countdown Tracker."""
import sqlite3
from datetime import datetime, date
from shared import db_path

DB_PATH = db_path("tabs", "countdown", "countdown.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def add_event(name, target_date):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO events (name, target_date) VALUES (?, ?)",
        (name, target_date)
    )
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return eid


def get_events():
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM events
        ORDER BY target_date ASC
    """).fetchall()
    conn.close()
    return rows


def delete_event(event_id):
    conn = get_db()
    conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


def days_until(target_date_str):
    """Returns (days_diff, label). Negative = passed, 0 = today, positive = upcoming."""
    target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    today = date.today()
    diff = (target - today).days
    if diff < 0:
        return abs(diff), "days ago"
    elif diff == 0:
        return 0, "today"
    else:
        return diff, "days left"
