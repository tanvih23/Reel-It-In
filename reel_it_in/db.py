"""SQLite event log — schema, writes, and replay queries."""

import sqlite3
import time
from pathlib import Path

from reel_it_in.config import EVENTS_DB

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_path  TEXT NOT NULL,
    question    TEXT NOT NULL,
    match       INTEGER NOT NULL,             -- sqlite has no bool: 0/1
    confidence  REAL NOT NULL,
    timestamp   REAL NOT NULL,                -- epoch seconds the event refers to
    status      TEXT NOT NULL DEFAULT 'passed',  -- 'passed' | 'review'
    created_at  REAL NOT NULL                 -- epoch seconds the row was written
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_question  ON events(question);
CREATE INDEX IF NOT EXISTS idx_events_status    ON events(status);
"""


def _db_path():
    path = EVENTS_DB or "./data/events.db"
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return path


def connect():
    """One connection per process (safety_worker, dashboard each call this once)."""
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")  # worker writes + dashboard reads concurrently
    conn.executescript(_SCHEMA)
    return conn


def insert_event(conn, event, chunk_path, status="passed"):
    """event: {"question", "match", "confidence", "timestamp"} — the shape
    middleware.threshold/dedup/prioritize already pass around."""
    conn.execute(
        """INSERT INTO events (chunk_path, question, match, confidence, timestamp, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            str(chunk_path),
            event["question"],
            1 if event["match"] else 0,
            float(event["confidence"]),
            float(event["timestamp"]),
            status,
            time.time(),
        ),
    )
    conn.commit()


def recent_events(conn, limit=50, status="passed"):
    """For the dashboard's live feed — most recent alerts first."""
    rows = conn.execute(
        "SELECT * FROM events WHERE status = ? ORDER BY timestamp DESC LIMIT ?",
        (status, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def events_since(conn, since_timestamp, status="passed"):
    """For polling loops (e.g. Streamlit autorefresh) — only what's new."""
    rows = conn.execute(
        "SELECT * FROM events WHERE status = ? AND timestamp > ? ORDER BY timestamp ASC",
        (status, since_timestamp),
    ).fetchall()
    return [dict(row) for row in rows]


def all_events(conn):
    """For eval/replay — the full log, chronological."""
    rows = conn.execute("SELECT * FROM events ORDER BY timestamp ASC").fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    conn = connect()
    print(f"DB at {_db_path()} — {len(all_events(conn))} events logged so far.")
    for row in recent_events(conn, limit=10):
        print(row)