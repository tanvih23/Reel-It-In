"""Feed-loss detection — flags when chunks stop arriving."""

# TODO: raise an alert if no new chunk lands within the expected interval
import time

last_chunk_time = time.time()

def record_chunk_received():
    global last_chunk_time
    last_chunk_time = time.time()

def check_feed_health(timeout_seconds=30):
    seconds_since_last_chunk = time.time() - last_chunk_time
    if seconds_since_last_chunk > timeout_seconds:
        return {"type": "feed_lost", "seconds_since_last_chunk": seconds_since_last_chunk}
    return None

if __name__ == "__main__":
    print("Checking immediately:", check_feed_health())

    record_chunk_received()
    print("Just received a chunk, checking again:", check_feed_health())

    print("Simulating a 35 second gap with no new chunks...")
    time.sleep(35)
    print("Checking after the gap:", check_feed_health())