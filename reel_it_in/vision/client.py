"""Shared Reka Vision API wrapper — used by both safety.py and highlights.py.

IMPORTANT: Reka's Chat API only accepts a real, fetchable HTTP(S) URL for
video_url content items — data URLs are documented as supported for
image_url only (https://docs.reka.ai/chat/chat-with-image-video-and-audio).
Passing a base64 data URL as video_url gets literally treated as a URL and
the server 400s trying to fetch it ("Could not fetch media from the URLs
provided").

Since our chunks are local files with nothing hosting them, we follow Reka's
own documented workaround for this exact case: extract frames locally and
send them as multiple image_url data URLs instead of one video_url.
"""

import base64
import io
import json
import mimetypes
import re

import av
from reka import ChatMessage
from reka.client import Reka

from reel_it_in.config import REKA_API_KEY

DEFAULT_MODEL = "reka-flash"
MAX_FRAMES = 6  # Reka's Chat API hard-caps media files at 6 per turn (confirmed via ApiError)

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Reka(api_key=REKA_API_KEY)
    return _client


def _extract_frames_jpeg(clip_path, num_frames=MAX_FRAMES):
    """Decode clip_path and return up to num_frames JPEG-encoded frame bytes,
    evenly spaced across the WHOLE clip. Reka caps media files at 6 per turn,
    so we can't sample at a fixed fps and cap after — that would only cover
    the first few seconds of a 15s chunk. This spans start to end instead."""
    container = av.open(str(clip_path))
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"

    all_frames = list(container.decode(stream))
    container.close()

    if not all_frames:
        raise ValueError(f"No frames could be decoded from {clip_path}")

    if len(all_frames) <= num_frames:
        sampled = all_frames
    else:
        step = len(all_frames) / num_frames
        sampled = [all_frames[int(i * step)] for i in range(num_frames)]

    jpeg_frames = []
    for frame in sampled:
        buf = io.BytesIO()
        frame.to_image().save(buf, format="JPEG", quality=85)
        jpeg_frames.append(buf.getvalue())
    return jpeg_frames


def _frames_to_content(clip_path):
    """The installed reka-api SDK validates content items against its own
    TypedMediaContent pydantic model (reka/types/typed_media_content.py),
    which wants a FLAT string for image_url — NOT the {"url": ...} nesting
    shown in Reka's OpenAI-compatible REST docs. That nested shape is for
    callers hitting the REST endpoint directly (e.g. via the openai package);
    reka-api builds and validates ChatMessage objects locally before that,
    so it enforces its own SDK-side schema instead."""
    content = []
    for jpeg_bytes in _extract_frames_jpeg(clip_path):
        b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
        content.append({
            "type": "image_url",
            "image_url": f"data:image/jpeg;base64,{b64}",
        })
    return content


def _build_prompt(questions):
    numbered = "\n".join(f'{i + 1}. "{q}"' for i, q in enumerate(questions))
    return (
        "These images are sequential frames sampled from a short clip at a "
        "public event, for crowd-safety monitoring. Judge only what is "
        "visibly happening across the frames — do not identify, describe, "
        "or track any individual person.\n\n"
        "For EACH question below, decide whether it matches this clip:\n"
        f"{numbered}\n\n"
        "Respond with ONLY a JSON array (no prose, no markdown fences), one "
        "object per question, in the same order, shaped exactly like:\n"
        '[{"question": "<question text>", "match": true, "confidence": 0.0}]\n'
        "confidence is your certainty in the match/no-match call, from 0.0 to 1.0."
    )


def _extract_text(response):
    """The reka-api SDK's chat.create() response shape. Falls back to the
    OpenAI-compatible shape in case the installed SDK version differs —
    verify against a live call and drop whichever branch you don't need."""
    try:
        return response.responses[0].message.content
    except AttributeError:
        pass
    try:
        return response.choices[0].message.content
    except AttributeError:
        pass
    raise RuntimeError(f"Unrecognized Reka response shape: {response!r}")


def _parse_json_array(raw_text, questions):
    cleaned = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        # Model didn't return clean JSON — fail safe rather than crash the
        # worker loop. All-zero confidence means threshold.py routes these
        # straight to the review queue instead of silently dropping them.
        print("Reka response wasn't valid JSON, routing to review:", raw_text[:200])
        return [{"question": q, "match": False, "confidence": 0.0} for q in questions]

    by_question = {item.get("question"): item for item in parsed if isinstance(item, dict)}
    results = []
    for q in questions:
        item = by_question.get(q, {})
        results.append({
            "question": q,
            "match": bool(item.get("match", False)),
            "confidence": float(item.get("confidence", 0.0)),
        })
    return results


def ask(clip_path, questions, model=DEFAULT_MODEL):
    """Send one video chunk (as sampled frames) + a batch of yes/no questions
    to Reka in a single call.

    Returns a list of {"question": str, "match": bool, "confidence": float},
    one per input question, in the same order.
    """
    frame_content = _frames_to_content(clip_path)

    response = get_client().chat.create(
        messages=[
            ChatMessage(
                role="user",
                content=[*frame_content, {"type": "text", "text": _build_prompt(questions)}],
            )
        ],
        model=model,
    )

    raw_text = _extract_text(response)
    return _parse_json_array(raw_text, questions)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m reel_it_in.vision.client <chunk_path> [\"question\" ...]")
        raise SystemExit(1)

    clip_path = sys.argv[1]
    questions = sys.argv[2:] or ["is anyone tightly surrounded", "is someone on the ground"]

    print(f"Extracting frames from {clip_path}...")
    frames = _extract_frames_jpeg(clip_path)
    print(f"  {len(frames)} frames, {sum(len(f) for f in frames) / 1024:.0f} KB total")

    print("Calling Reka...")
    for result in ask(clip_path, questions):
        print(" ", result)