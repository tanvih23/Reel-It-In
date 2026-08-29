"""Generate on-screen captions and social media caption suggestions."""

from typing import Any

_CAPTION_STYLES = [
    (("dancing", "cheering"), "🎉 Crowd going wild"),
    (("stage", "performance"), "🔥 Center stage moment"),
    (("confetti", "streamers", "lights"), "✨ Pure magic"),
    (("coordinated", "celebration"), "🙌 Everyone together"),
    (("funny", "surprising", "unusual"), "😂 Unexpected moment"),
]

_DEFAULT_CAPTION = "✨ Highlight moment"


def overlay_text(highlight: dict[str, Any]) -> str:
    """Return a short on-screen caption for one highlight clip."""

    text_source = f"{highlight.get('query', '')} {highlight.get('reason', '')}".lower()

    for keywords, caption in _CAPTION_STYLES:
        if any(keyword in text_source for keyword in keywords):
            return caption

    return _DEFAULT_CAPTION


def suggest_post_caption(highlights: list[dict[str, Any]]) -> str:
    """Build a suggested social media caption + hashtags for the whole reel."""

    moments = sorted({overlay_text(h) for h in highlights})
    body = " | ".join(moments) if moments else "The best moments, all in one reel."
    hashtags = "#Highlights #CollegeFest #ReelItIn #BestMoments"

    return f"{body}\n\n{hashtags}"