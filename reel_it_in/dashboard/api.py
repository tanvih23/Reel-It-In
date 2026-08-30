"""FastAPI backend for the dashboard — exposes SQLite to the React frontend.

Run: uvicorn reel_it_in.dashboard.api:app --reload --port 8000
"""

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from reel_it_in import db

app = FastAPI(title="Reel-It-In Dashboard API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

conn = db.connect()


@app.get("/api/events")
def get_events(since: float = 0, status: str = "passed", limit: int = 100):
    """Polled by the frontend every few seconds."""
    if since > 0:
        rows = db.events_since(conn, since, status=status)
    else:
        rows = db.recent_events(conn, limit=limit, status=status)
    return {"events": rows, "server_time": time.time()}


@app.get("/api/stats")
def get_stats():
    """Quick summary numbers for the top cards."""
    all_rows = db.all_events(conn)
    passed = [r for r in all_rows if r["status"] == "passed"]
    review = [r for r in all_rows if r["status"] == "review"]

    turbulent = [r for r in passed if "turbulent" in r["question"]]
    reka_alerts = [r for r in passed if "turbulent" not in r["question"]
                   and "pulsing" not in r["question"]]

    return {
        "total_alerts": len(passed),
        "review_queue": len(review),
        "turbulence_detections": len(turbulent),
        "reka_alerts": len(reka_alerts),
        "server_time": time.time(),
    }