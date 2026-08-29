"""Shared Reka Vision API wrapper — used by both safety.py and highlights.py."""
"""Shared Reka Vision API wrapper — used by both safety.py and highlights.py.

Chunks are 15s, well under the 30s cutoff where Reka's docs say to use the
Chat API's multimodal video input directly rather than the separate
upload-and-index Vision API (that's for longer, searchable video libraries —
overkill, and slower, for a chunk we're about to purge anyway).
"""

import base64
import json
import mimetypes
import re

from reka import ChatMessage
from reka.client import Reka

from reel_it_in.config import REKA_API_KEY

DEFAULT_MODEL = "reka-flash"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Reka(api_key=REKA_API_KEY)
    return _client


def _video_to_data_url(clip_path):
    mime_type, _ = mimetypes.guess_type(str(clip_path))
    mime_type = mime_type or "video/mp4"
    with open(clip_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def _build_prompt(questions):
    numbered = "\n".join(f'{i + 1}. "{q}"' for i, q in enumerate(questions))
    return (
        "You are reviewing a short clip from a public event for crowd-safety "
        "monitoring. Judge only what is visibly happening in the clip — do not "
        "identify, describe, or track any individual person.\n\n"
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
    """Send one video chunk + a batch of yes/no questions to Reka in a single call.

    Returns a list of {"question": str, "match": bool, "confidence": float},
    one per input question, in the same order.
    """
    video_data_url = _video_to_data_url(clip_path)

    response = get_client().chat.create(
        messages=[
            ChatMessage(
                role="user",
                content=[
                    {"type": "video_url", "video_url": video_data_url},
                    {"type": "text", "text": _build_prompt(questions)},
                ],
            )
        ],
        model=model,
    )

    raw_text = _extract_text(response)
    return _parse_json_array(raw_text, questions)
