"""Dedup — collapses the same concern repeating across consecutive chunks."""

# TODO: suppress repeats within a time window so one incident is one alert
recent_alerts = []

def dedup(event, window_seconds=45):
    for alert in recent_alerts:
        same_question = alert["question"] == event["question"]
        recent_enough = (event["timestamp"] - alert["timestamp"]) < window_seconds

        if same_question and recent_enough:
            alert["timestamp"] = event["timestamp"]
            return None

    new_alert = {
        "question": event["question"],
        "timestamp": event["timestamp"],
    }
    recent_alerts.append(new_alert)
    return new_alert

if __name__ == "__main__":
    event1 = {"question": "is anyone tightly surrounded", "timestamp": 15}
    event2 = {"question": "is anyone tightly surrounded", "timestamp": 30}
    event3 = {"question": "is anyone tightly surrounded", "timestamp": 90}

    print(dedup(event1))
    print(dedup(event2))
    print(dedup(event3))