"""Entrypoint for `python -m reel_it_in.vision.safety_worker`. Owner: Tanvi."""

import sys
import time
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parents[1]
if str(_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_DIR))

from reel_it_in import db
from reel_it_in.config import CHUNK_DIR
from reel_it_in.middleware.dedup import dedup
from reel_it_in.middleware.feed_loss import check_feed_health, record_chunk_received
from reel_it_in.middleware.prioritize import rank_alerts
from reel_it_in.middleware.threshold import filter_by_confidence
from reel_it_in.vision.safety import analyze

POLL_SECONDS = 2


def _pending_chunks(chunk_dir):
    """New .mp4 chunks not yet analyzed, oldest first."""
    return sorted(Path(chunk_dir).glob("*.mp4"), key=lambda p: p.stat().st_mtime)


def process_chunk(chunk_path, conn):
    record_chunk_received()

    try:
        raw_events = analyze(str(chunk_path))
    except Exception as exc:
        # A single bad Reka call (timeout, transient API error) shouldn't
        # take down the live monitoring loop.
        print(f"[ERROR] analyze failed for {chunk_path.name}: {exc}")
        chunk_path.unlink(missing_ok=True)
        return

    # Order matches readme.md's architecture diagram: threshold -> dedup -> prioritize
    passed, review_queue = filter_by_confidence(raw_events)

    for event in review_queue:
        db.insert_event(conn, event, chunk_path=chunk_path, status="review")

    survivors = []
    for event in passed:
        # dedup() only returns a trimmed {question, timestamp} dict (or None
        # if suppressed) — used here purely as the suppression signal. The
        # full event (with confidence) is what gets stored and ranked.
        if dedup(event) is None:
            continue
        survivors.append(event)
        db.insert_event(conn, event, chunk_path=chunk_path, status="passed")

    if survivors:
        for alert in rank_alerts(survivors, time.time()):
            print(f"[ALERT] {alert['question']} (confidence {alert['confidence']:.2f})")

    # No footage retained, by design (see readme.md "No identity, ever")
    chunk_path.unlink(missing_ok=True)


def run():
    chunk_dir = Path(CHUNK_DIR or "./data/chunks")
    chunk_dir.mkdir(parents=True, exist_ok=True)

    conn = db.connect()
    print(f"Watching {chunk_dir} for new chunks...")

    while True:
        feed_alert = check_feed_health()
        if feed_alert:
            print(f"[WARN] {feed_alert}")

        for chunk_path in _pending_chunks(chunk_dir):
            process_chunk(chunk_path, conn)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run()
