import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            title TEXT NOT NULL,
            artist TEXT DEFAULT 'Unknown',
            album TEXT DEFAULT 'Unknown',
            duration REAL DEFAULT 0,
            track_order INTEGER NOT NULL,
            FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_setting(key, value):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def create_playlist(name):
    conn = get_db()
    try:
        cur = conn.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
        conn.commit()
        pid = cur.lastrowid
        return pid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def delete_playlist(playlist_id):
    conn = get_db()
    conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    conn.commit()
    conn.close()


def get_all_playlists():
    conn = get_db()
    rows = conn.execute(
        "SELECT p.*, COUNT(pt.id) as track_count "
        "FROM playlists p LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id "
        "GROUP BY p.id ORDER BY p.name"
    ).fetchall()
    conn.close()
    return rows


def add_track_to_playlist(playlist_id, track, order):
    conn = get_db()
    conn.execute(
        "INSERT INTO playlist_tracks (playlist_id, file_path, title, artist, album, duration, track_order) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (playlist_id, track["file_path"], track["title"], track["artist"],
         track["album"], track.get("duration", 0), order)
    )
    conn.commit()
    conn.close()


def get_playlist_tracks(playlist_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM playlist_tracks WHERE playlist_id = ? ORDER BY track_order",
        (playlist_id,)
    ).fetchall()
    conn.close()
    return rows


def clear_playlist_tracks(playlist_id):
    conn = get_db()
    conn.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
    conn.commit()
    conn.close()
