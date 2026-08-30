"""Generate captions for highlight clips."""

from typing import Any


CAPTION_STYLES = [
    (("dancing", "cheering"), ""), #🎉 Crowd going wild
    (("stage", "performance"), ""), #Center stage moment
    (("confetti", "streamers", "lights"), ""), #✨ Pure magic
    (("coordinated", "celebration"), ""),#🙌 Everyone together
    (("funny", "surprising", "unusual"), ""),#😂 Unexpected moment
]

DEFAULT_CAPTION = "✨ Highlight moment"


def overlay_text(highlight: dict[str, Any]) -> str:
    """Generate a short caption for one highlight."""

    text = (
        f"{highlight.get('query', '')} "
        f"{highlight.get('reason', '')}"
    ).lower()

    for keywords, caption in CAPTION_STYLES:
        if any(keyword in text for keyword in keywords):
            return caption

    return DEFAULT_CAPTION


def suggest_post_caption(highlights: list[dict[str, Any]]) -> str:
    """Generate a social-media caption for the complete reel."""

    moments = []

    for highlight in highlights:
        caption = overlay_text(highlight)

        if caption not in moments:
            moments.append(caption)

    if moments:
        body = " | ".join(moments)
    else:
        body = "The best moments, all in one reel."

    hashtags = "#Highlights #CollegeFest #ReelItIn #BestMoments"

    return f"{body}\n\n{hashtags}"