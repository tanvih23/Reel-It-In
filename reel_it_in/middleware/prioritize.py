"""Alert ranking — orders surviving alerts for the monitor's attention."""

# TODO: score by severity and recency so the dashboard sorts sensibly
SEVERITY_SCORES = {
    "crowd flow is turbulent": 12,
    "is someone on the ground and looks like they have fainted": 10,
    "is anyone laying on the ground": 10,
    "does someone look injured": 9,
    "is anyone tightly surrounded": 8,
    "crowd movement is pulsing in stop-and-go waves": 7,
    "is there a sudden bunching of the crowd": 6,
    "is the crowd rushing towards a single direction": 5,
}

def get_priority_score(alert, current_time):
    severity = SEVERITY_SCORES.get(alert["question"], 1)
    age_seconds = current_time - alert["timestamp"]
    recency_score = max(0, 100 - age_seconds)
    return severity * 10 + recency_score

def rank_alerts(alerts, current_time):
    return sorted(
        alerts,
        key=lambda alert: (
            SEVERITY_SCORES.get(alert["question"], 1),
            -(current_time - alert["timestamp"])
        ),
        reverse=True
    )


if __name__ == "__main__":
    import time
    now = time.time()

    fake_alerts = [
    {"question": "is anyone tightly surrounded", "timestamp": now - 10},
    {"question": "is someone on the ground and looks like they have fainted", "timestamp": now - 60},
    {"question": "is there a sudden bunching of the crowd", "timestamp": now - 5},
    {"question": "crowd flow is turbulent", "timestamp": now - 90},
]

    ranked = rank_alerts(fake_alerts, now)
    for alert in ranked:
        print(alert["question"], "| score:", get_priority_score(alert, now))