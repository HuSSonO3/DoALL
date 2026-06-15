"""Calorie Budgeter — SQLite persistence and calculation logic."""

import sqlite3
from datetime import date, timedelta

from shared import db_path

DB_PATH = db_path("tabs", "calorie_budgeter", "calories.db")

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id      INTEGER PRIMARY KEY CHECK(id = 1),
            weight  REAL    NOT NULL,
            height  REAL    NOT NULL,
            age     INTEGER NOT NULL,
            gender  TEXT    NOT NULL,
            activity TEXT   NOT NULL,
            goal_kg_per_week REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            date     TEXT    NOT NULL,
            label    TEXT    NOT NULL,
            calories INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ── Profile ──


def get_profile():
    conn = get_db()
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def save_profile(weight, height, age, gender, activity, goal_kg_per_week):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO profile (id, weight, height, age, gender, activity, goal_kg_per_week)
        VALUES (1, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            weight           = excluded.weight,
            height           = excluded.height,
            age              = excluded.age,
            gender           = excluded.gender,
            activity         = excluded.activity,
            goal_kg_per_week = excluded.goal_kg_per_week
    """,
        (weight, height, age, gender, activity, goal_kg_per_week),
    )
    conn.commit()
    conn.close()


# ── Logs ──


def add_log(label, calories):
    conn = get_db()
    conn.execute(
        "INSERT INTO logs (date, label, calories) VALUES (?, ?, ?)",
        (date.today().isoformat(), label, calories),
    )
    conn.commit()
    conn.close()


def delete_log(entry_id):
    conn = get_db()
    conn.execute("DELETE FROM logs WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


def get_today_logs():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, label, calories FROM logs WHERE date = ? ORDER BY rowid ASC",
        (date.today().isoformat(),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_week_logs():
    """Return all entries for Mon–today, ordered by date then insertion order."""
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT id, date, label, calories FROM logs "
        "WHERE date >= ? AND date <= ? ORDER BY date ASC, rowid ASC",
        (week_start, today.isoformat()),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_total():
    conn = get_db()
    row = conn.execute(
        "SELECT COALESCE(SUM(calories), 0) FROM logs WHERE date = ?",
        (date.today().isoformat(),),
    ).fetchone()
    conn.close()
    return row[0]


def get_week_total():
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()
    conn = get_db()
    row = conn.execute(
        "SELECT COALESCE(SUM(calories), 0) FROM logs WHERE date >= ?",
        (week_start,),
    ).fetchone()
    conn.close()
    return row[0]


# ── Calculations ──


def calculate_targets(profile):
    """Return (weekly_budget, daily_target, tdee) from a profile dict.

    Uses the Mifflin-St Jeor equation for BMR, then applies an activity
    multiplier for TDEE.  The weekly deficit is computed as:
        1 kg of fat ≈ 7700 kcal
    so the weekly calorie budget is TDEE*7 minus the chosen weekly deficit.
    """
    w = profile["weight"]
    h = profile["height"]
    a = profile["age"]
    g = profile["gender"]
    act = profile["activity"]
    goal = profile["goal_kg_per_week"]

    # Mifflin-St Jeor BMR
    bmr = 10 * w + 6.25 * h - 5 * a + (5 if g == "male" else -161)

    tdee = bmr * ACTIVITY_MULTIPLIERS.get(act, 1.2)

    weekly_budget = tdee * 7 - goal * 7700
    daily_target = weekly_budget / 7

    return round(weekly_budget), round(daily_target), round(tdee)


def get_dynamic_daily_target(weekly_budget):
    """Re-balance the daily target across remaining days of the week.

    If the user over-ate yesterday, today's allowance shrinks automatically.
    """
    today = date.today()
    days_remaining = 7 - today.weekday()  # Mon=0 → 7 days left today
    week_consumed = get_week_total()
    remaining = weekly_budget - week_consumed
    if days_remaining <= 0:
        return 0
    return round(remaining / days_remaining)
