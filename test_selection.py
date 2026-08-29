from reel_it_in.highlights.selection import select_highlights


print("===================================")
print("     HIGHLIGHT SELECTION TEST")
print("===================================")


# Fake Reka results for testing.
# These imitate what Reka gives us.

events = [
    {
        "start": 0.0,
        "end": 21.04,
        "score": 0.924,
        "reason": "large coordinated crowd reaction",
    },
    {
        "start": 0.0,
        "end": 21.04,
        "score": 0.923,
        "reason": "large crowd dancing",
    },
    {
        "start": 0.0,
        "end": 21.04,
        "score": 0.920,
        "reason": "stage performance",
    },
    {
        "start": 30.0,
        "end": 40.0,
        "score": 0.900,
        "reason": "audience cheering",
    },
    {
        "start": 50.0,
        "end": 60.0,
        "score": 0.850,
        "reason": "funny moment",
    },
]


selected = select_highlights(
    events,
    max_highlights=5,
)


print()
print(
    f"Reka returned {len(events)} candidate highlights."
)

print()
print(
    f"Selected {len(selected)} highlights:"
)

for i, highlight in enumerate(selected, start=1):

    duration = (
        highlight["end"]
        - highlight["start"]
    )

    print()
    print(f"Highlight {i}")
    print(
        f"  Time: "
        f"{highlight['start']:.2f}s → "
        f"{highlight['end']:.2f}s"
    )
    print(
        f"  Duration: {duration:.2f}s"
    )
    print(
        f"  Score: {highlight['score']:.3f}"
    )
    print(
        f"  Reason: {highlight['reason']}"
    )