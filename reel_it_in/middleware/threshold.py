"""Confidence gating — drops events below CONFIDENCE_THRESHOLD. Owner: Kirtika."""

# TODO: filter raw vision events against the configured threshold
from config import CONFIDENCE_THRESHOLD

def filter_by_confidence(events):
    passed = []
    review_queue = []

    for event in events:
        if event["confidence"] >= CONFIDENCE_THRESHOLD:
            passed.append(event)
        else:
            review_queue.append(event)

    return passed, review_queue
if __name__ == "__main__":
    fake_events = [
        {"question": "is anyone tightly surrounded", "match": True, "confidence": 0.82, "timestamp": 15},
        {"question": "is someone on the ground", "match": False, "confidence": 0.20, "timestamp": 15},
    ]

    good, review = filter_by_confidence(fake_events)
    print("Passed threshold:", good)
    print("Sent to review:", review)