"""SQLite persistence for the Job Interview Tracker."""
import sqlite3
from datetime import datetime
from shared import db_path

DB_PATH = db_path("tabs", "job_tracker", "job_tracker.db")

STATUSES = [
    "Applied", "Waiting", "Interviewing", "Follow-up",
    "Offer", "Accepted", "Rejected", "Ghosted",
]

TYPES = ["On-site", "Hybrid", "Remote"]

# Countries with decent tech prospects for foreign workers + their currency symbols
COUNTRIES = {
    "Australia":        "AU$",
    "Austria":          "€",
    "Belgium":          "€",
    "Brazil":           "R$",
    "Canada":           "CA$",
    "Czech Republic":   "Kč",
    "Denmark":          "kr",
    "Estonia":          "€",
    "Finland":          "€",
    "France":           "€",
    "Germany":          "€",
    "Ireland":          "€",
    "Luxembourg":       "€",
    "Malaysia":         "RM",
    "Netherlands":      "€",
    "New Zealand":      "NZ$",
    "Norway":           "kr",
    "Poland":           "zł",
    "Portugal":         "€",
    "Singapore":        "S$",
    "South Korea":      "₩",
    "Spain":            "€",
    "Sweden":           "kr",
    "Switzerland":      "CHF",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            job_title TEXT NOT NULL,
            salary TEXT NOT NULL,
            salary_per TEXT NOT NULL DEFAULT 'year',
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Applied',
            reason TEXT DEFAULT '',
            stage TEXT DEFAULT '',
            url TEXT NOT NULL,
            country TEXT NOT NULL,
            remarks TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    # Migration: add salary_per column if upgrading from older schema
    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN salary_per TEXT NOT NULL DEFAULT 'year'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()


def currency_for(country):
    return COUNTRIES.get(country, "$")


# ── CRUD ──

def add_job(company_name, job_title, salary, salary_per, type, status, country, url,
            reason="", stage="", remarks=""):
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur = conn.execute("""
        INSERT INTO jobs (company_name, job_title, salary, salary_per, type, status,
                          country, url, reason, stage, remarks, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (company_name, job_title, salary, salary_per, type, status, country, url,
          reason, stage, remarks, now))
    conn.commit()
    jid = cur.lastrowid
    conn.close()
    return jid


def update_job(job_id, company_name, job_title, salary, salary_per, type, status,
               country, url, reason, stage, remarks):
    conn = get_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute("""
        UPDATE jobs SET
            company_name = ?, job_title = ?, salary = ?, salary_per = ?, type = ?, status = ?,
            country = ?, url = ?, reason = ?, stage = ?, remarks = ?, updated_at = ?
        WHERE id = ?
    """, (company_name, job_title, salary, salary_per, type, status, country, url,
          reason, stage, remarks, now, job_id))
    conn.commit()
    conn.close()


def delete_job(job_id):
    conn = get_db()
    conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()


def get_jobs(country=None, status=None, search=None):
    conn = get_db()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if country:
        query += " AND country = ?"
        params.append(country)
    if status:
        query += " AND status = ?"
        params.append(status)
    if search:
        query += " AND company_name LIKE ?"
        params.append(f"%{search}%")
    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def auto_ghost_old_applied():
    """Change 'Applied' jobs older than 2 weeks to 'Ghosted'."""
    conn = get_db()
    conn.execute("""
        UPDATE jobs SET status = 'Ghosted', updated_at = datetime('now')
        WHERE status = 'Applied'
          AND julianday('now') - julianday(updated_at) > 14
    """)
    conn.commit()
    conn.close()


def get_distinct_countries():
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT country FROM jobs ORDER BY country"
    ).fetchall()
    conn.close()
    return [r["country"] for r in rows]
