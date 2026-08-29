"""Safety question set and Reka caller. Owner: Tanvi."""

import time

from reel_it_in.vision.client import ask

SAFETY_QUESTIONS = [
    "is anyone tightly surrounded",
    "is there a sudden bunching of the crowd",
    "is someone on the ground and looks like they have fainted", 
    "does someone look injured", 
    "is the crowd rushing towards a single direction",
    "is anyone laying on the ground",
]


def analyze(chunk_path):
    """Run the safety question set against one video chunk.

    Returns a list of scored events shaped exactly like fake_safety.analyze()
    and what middleware.threshold/dedup/prioritize already expect:
        {"question": str, "match": bool, "confidence": float, "timestamp": float}

    `timestamp` is wall-clock epoch seconds at analysis time — not seconds
    into the clip. dedup's window check and prioritize's recency scoring
    both do `current_time - event["timestamp"]`, so this has to be real
    epoch time to line up with feed_loss.py, which also uses time.time().
    """
    raw_results = ask(chunk_path, SAFETY_QUESTIONS)
    now = time.time()

    return [
        {
            "question": result["question"],
            "match": result["match"],
            "confidence": result["confidence"],
            "timestamp": now,
        }
        for result in raw_results
    ]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m reel_it_in.vision.safety <chunk_path>")
    else:
        for event in analyze(sys.argv[1]):
            print(event)
