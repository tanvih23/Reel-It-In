"""Find exciting moments in a video using Reka Vision."""

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# Reka Vision API
BASE_URL = "https://vision-agent.api.reka.ai"


# Get API key from .env
REKA_API_KEY = os.getenv("REKA_API_KEY")

if not REKA_API_KEY:
    raise RuntimeError(
        "REKA_API_KEY is missing. Add it to the project's .env file."
    )


# Authentication header
HEADERS = {
    "X-Api-Key": REKA_API_KEY,
}


# Questions we will ask Reka
HIGHLIGHT_QUERIES = [
    "large crowd dancing and cheering enthusiastically",
    "exciting stage performance with energetic audience reaction",
    "confetti, streamers, dramatic lights, or visually spectacular moment",
    "large coordinated crowd reaction or celebration",
    "funny surprising or unusual memorable moment at a college festival",
]


def upload_video(video_path: str) -> str:
    """Upload a video to Reka and return its video ID."""

    # Make sure the file exists
    if not os.path.isfile(video_path):
        raise FileNotFoundError(
            f"Video file does not exist: {video_path}"
        )

    url = f"{BASE_URL}/v1/videos/upload"

    data = {
        "index": "true",
        "video_name": os.path.basename(video_path),
    }

    print(f"\n[Reka] Uploading video: {video_path}")

    with open(video_path, "rb") as video_file:

        files = {
            "file": (
                os.path.basename(video_path),
                video_file,
                "video/mp4",
            )
        }

        response = requests.post(
            url,
            headers=HEADERS,
            data=data,
            files=files,
            timeout=300,
        )

    # Raise an error if Reka rejected the request
    response.raise_for_status()

    result = response.json()

    video_id = result.get("video_id")

    if not video_id:
        raise RuntimeError(
            f"Upload succeeded but no video_id was returned: {result}"
        )

    print("[Reka] Upload successful!")
    print(f"[Reka] Video ID: {video_id}")

    return video_id


def wait_until_indexed(
    video_id: str,
    timeout_seconds: int = 600,
    poll_seconds: int = 5,
) -> dict[str, Any]:
    """Wait until Reka finishes indexing the uploaded video."""

    url = f"{BASE_URL}/v1/videos/{video_id}"

    start_time = time.time()

    print("\n[Reka] Waiting for video indexing...")

    while True:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        result = response.json()

        status = result.get("indexing_status")

        print(f"[Reka] Indexing status: {status}")

        if status == "indexed":
            print("[Reka] Video is ready!")
            return result

        if status == "failed":
            raise RuntimeError(
                f"Reka failed to index video {video_id}"
            )

        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(
                "Timed out while waiting for Reka to index the video."
            )

        time.sleep(poll_seconds)


def search_highlights(
    video_id: str,
    query: str,
    max_results: int = 5,
    threshold: float = 0.30,
    max_retries: int = 2,
) -> list[dict[str, Any]]:
    """Search the video for moments matching one highlight query."""

    url = f"{BASE_URL}/v1/videos/search"

    payload = {
        "query": query,
        "video_ids": [video_id],
        "max_results": max_results,
        "threshold": threshold,
        "generate_report": False,
    }

    print(f"\n[Reka] Searching for: {query}")

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                url,
                headers={
                    **HEADERS,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            result = response.json()
            matches = result.get("results", [])

            print(f"[Reka] Found {len(matches)} matching moments.")
            return matches

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
            last_error = error
            print(
                f"[Reka] Attempt {attempt}/{max_retries} failed "
                f"({type(error).__name__}). Retrying..."
            )
            time.sleep(3)

    # If we get here, every retry failed
    print(
        f"[Reka] Giving up on query after {max_retries} attempts: {query}"
    )
    print(f"[Reka] Last error: {last_error}")
    return []

def find_highlights(video_id: str) -> list[dict[str, Any]]:
    """Run all highlight searches and return timestamped events."""

    events = []

    for query in HIGHLIGHT_QUERIES:

        matches = search_highlights(
            video_id=video_id,
            query=query,
            max_results=5,
            threshold=0.30,
        )

        for match in matches:

            start = match.get("start_timestamp")
            end = match.get("end_timestamp")

            if start is None or end is None:
                continue

            events.append(
                {
                    "start": float(start),
                    "end": float(end),
                    "score": float(match.get("score") or 0),
                    "reason": match.get(
                        "explanation",
                        query,
                    ),
                    "query": query,
                }
            )

    # Sort best matches first
    events.sort(
        key=lambda event: event["score"],
        reverse=True,
    )

    return events