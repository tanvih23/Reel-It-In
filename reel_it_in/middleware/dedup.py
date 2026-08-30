"""Dedup — collapses the same concern repeating across consecutive chunks."""

# TODO: suppress repeats within a time window so one incident is one alert
FLOW_QUESTIONS = {
    "crowd flow is turbulent",
    "crowd movement is pulsing in stop-and-go waves",
}
recent_alerts = []

def dedup(event, window_seconds=45, flow_window_seconds=5):
    global recent_alerts
    recent_alerts = [a for a in recent_alerts if (event["timestamp"] - a["timestamp"]) < 300]

    is_flow = event["question"] in FLOW_QUESTIONS
    effective_window = flow_window_seconds if is_flow else window_seconds

    for alert in recent_alerts:
        same_question = alert["question"] == event["question"]
        recent_enough = (event["timestamp"] - alert["timestamp"]) < effective_window

        if same_question and recent_enough:
            alert["timestamp"] = event["timestamp"]
            alert["repeat_count"] = alert.get("repeat_count", 1) + 1
            if is_flow:
                return alert
            return None

    new_alert = {
        "question": event["question"],
        "timestamp": event["timestamp"],
        "repeat_count": 1,
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

    print("--- flow question, should NOT go silent ---")
    flow1 = {"question": "crowd flow is turbulent", "timestamp": 100}
    flow2 = {"question": "crowd flow is turbulent", "timestamp": 103}
    flow3 = {"question": "crowd flow is turbulent", "timestamp": 106}

    print(dedup(flow1))
    print(dedup(flow2))
    print(dedup(flow3))