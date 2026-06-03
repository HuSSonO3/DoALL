"""Currency rate cache — fetched once a day from open.er-api.com (free, no key)."""
import sqlite3
import json
import time
import urllib.request
from shared import db_path

DB_PATH = db_path("tabs", "unit_converter", "unit_converter.db")

API_URL = "https://open.er-api.com/v6/latest/USD"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS currency_cache (
            key TEXT PRIMARY KEY,
            rates_json TEXT NOT NULL,
            fetched_at REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def _fetch_fresh():
    """Fetch rates from API and cache them. Returns (rates dict, timestamp)."""
    try:
        req = urllib.request.Request(API_URL, headers={"User-Agent": "DoALL/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None, None

    rates = data.get("rates", {})
    ts = data.get("time_last_update_unix", time.time())

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO currency_cache (key, rates_json, fetched_at) VALUES (?, ?, ?)",
        ("latest", json.dumps(rates), ts)
    )
    conn.commit()
    conn.close()
    return rates, ts


def get_rates():
    """Return (rates dict, last_fetched_timestamp). Refetches if older than 24h."""
    conn = get_db()
    row = conn.execute(
        "SELECT rates_json, fetched_at FROM currency_cache WHERE key = 'latest'"
    ).fetchone()
    conn.close()

    now = time.time()
    if row and (now - row["fetched_at"]) < 86400:  # 24 hours
        return json.loads(row["rates_json"]), row["fetched_at"]

    return _fetch_fresh()
