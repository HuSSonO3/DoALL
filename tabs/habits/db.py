"""Habit Tracker — SQLite persistence."""

import sqlite3
from datetime import datetime, timedelta
from shared import db_path

DB_PATH = db_path("tabs", "habits", "habits.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS habit_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
            UNIQUE(habit_id, date)
        )
    """)
    conn.commit()
    conn.close()


# ── Habits CRUD ──

def add_habit(name):
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO habits (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_habits():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM habits ORDER BY created_at ASC"
    ).fetchall()
    conn.close()
    return rows


def update_habit(habit_id, name):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE habits SET name = ? WHERE id = ?", (name, habit_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_habit(habit_id):
    conn = get_db()
    conn.execute("DELETE FROM habit_entries WHERE habit_id = ?", (habit_id,))
    conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()


# ── Entries ──

def toggle_entry(habit_id, date_str):
    """Toggle a habit entry for a given date. Returns True if now completed, False if unmarked."""
    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM habit_entries WHERE habit_id = ? AND date = ?",
        (habit_id, date_str)
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM habit_entries WHERE id = ?", (existing["id"],))
        conn.commit()
        conn.close()
        return False
    else:
        conn.execute(
            "INSERT INTO habit_entries (habit_id, date) VALUES (?, ?)",
            (habit_id, date_str)
        )
        conn.commit()
        conn.close()
        return True


def is_completed(habit_id, date_str):
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM habit_entries WHERE habit_id = ? AND date = ?",
        (habit_id, date_str)
    ).fetchone()
    conn.close()
    return row is not None


def get_week_entries(habit_id, monday_str):
    """Return a dict of date_str -> bool for Mon-Sun of the week starting at monday_str."""
    monday = datetime.strptime(monday_str, "%Y-%m-%d")
    dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

    conn = get_db()
    rows = conn.execute(
        """SELECT date FROM habit_entries
           WHERE habit_id = ? AND date >= ? AND date <= ?""",
        (habit_id, dates[0], dates[6])
    ).fetchall()
    conn.close()

    completed_dates = {r["date"] for r in rows}
    return {d: d in completed_dates for d in dates}


def get_streak(habit_id, today_str=None):
    """Calculate current streak (consecutive days ending at today_str or yesterday).
    Returns (streak, longest_streak)."""
    if today_str is None:
        today_str = datetime.now().strftime("%Y-%m-%d")

    conn = get_db()
    rows = conn.execute(
        "SELECT date FROM habit_entries WHERE habit_id = ? ORDER BY date ASC",
        (habit_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return 0, 0

    completed = {r["date"] for r in rows}

    # Current streak: count backwards from today (or yesterday if today not done)
    today = datetime.strptime(today_str, "%Y-%m-%d")
    check_date = today if today_str in completed else today - timedelta(days=1)
    current_streak = 0
    while check_date.strftime("%Y-%m-%d") in completed:
        current_streak += 1
        check_date -= timedelta(days=1)

    # Longest streak
    all_dates = sorted(completed)
    longest = 0
    run = 0
    prev = None
    for d in all_dates:
        dt = datetime.strptime(d, "%Y-%m-%d")
        if prev is None:
            run = 1
        elif (dt - prev).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = dt
    longest = max(longest, run)

    return current_streak, longest


def get_completion_rate(habit_id):
    """Return fraction of days completed since habit was created."""
    conn = get_db()
    habit = conn.execute("SELECT created_at FROM habits WHERE id = ?", (habit_id,)).fetchone()
    if not habit:
        conn.close()
        return 0.0

    total_days = (datetime.now() - datetime.strptime(
        habit["created_at"][:10], "%Y-%m-%d"
    )).days + 1

    count = conn.execute(
        "SELECT COUNT(*) as n FROM habit_entries WHERE habit_id = ?", (habit_id,)
    ).fetchone()["n"]
    conn.close()

    if total_days <= 0:
        return 0.0
    return count / total_days
