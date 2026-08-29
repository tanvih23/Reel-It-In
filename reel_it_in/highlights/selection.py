"""Select the best non-overlapping highlights from Reka results."""

from typing import Any


def overlaps(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:
    """Return True if two highlights overlap in time."""

    return (
        first["start"] < second["end"]
        and second["start"] < first["end"]
    )


def select_highlights(
    events: list[dict[str, Any]],
    max_highlights: int = 5,
    min_gap: float = 2.0,
    target_duration: float = 30.0,
) -> list[dict[str, Any]]:
    """
    Select the best highlights while avoiding duplicates,
    stopping once the reel reaches roughly target_duration seconds.

    Parameters:
        events:
            Candidate highlights returned by Reka.

        max_highlights:
            Maximum number of highlights to keep.

        min_gap:
            Minimum gap between selected highlights in seconds.

        target_duration:
            Desired total length of the final reel, in seconds.
            The function stops adding clips once this is reached,
            trimming the last clip if needed to land exactly on it.

    Returns:
        A list of selected highlights whose combined length is
        approximately target_duration seconds.
    """

    if not events:
        return []

    # --------------------------------------------------
    # 1. Sort candidates by Reka's score
    # --------------------------------------------------

    candidates = sorted(
        events,
        key=lambda event: event.get("score", 0),
        reverse=True,
    )

    selected = []
    total_duration = 0.0

    # --------------------------------------------------
    # 2. Go through the candidates
    # --------------------------------------------------

    for candidate in candidates:

        start = float(candidate["start"])
        end = float(candidate["end"])

        # Ignore invalid timestamps
        if end <= start:
            continue

        # --------------------------------------------------
        # 3. Check whether this overlaps an already
        #    selected highlight
        # --------------------------------------------------

        too_close = False

        for existing in selected:

            if overlaps(candidate, existing):
                too_close = True
                break

            # Also avoid clips that are almost touching.
            if (
                abs(start - existing["end"]) < min_gap
                or abs(existing["start"] - end) < min_gap
            ):
                too_close = True
                break

        if too_close:
            continue

        # --------------------------------------------------
        # 4. Check the duration budget
        # --------------------------------------------------

        clip_duration = end - start
        remaining = target_duration - total_duration

        # We've already hit the target length; stop entirely.
        if remaining <= 0:
            break

        # This clip fits within budget as-is.
        if clip_duration <= remaining:
            selected.append(candidate)
            total_duration += clip_duration

        # This clip is longer than the remaining budget:
        # trim it down so the reel lands exactly on target_duration.
        else:
            trimmed = dict(candidate)
            trimmed["end"] = start + remaining
            selected.append(trimmed)
            total_duration += remaining
            break  # Budget is now full.

        if len(selected) >= max_highlights:
            break

    # --------------------------------------------------
    # 5. Sort selected highlights chronologically
    # --------------------------------------------------

    selected.sort(
        key=lambda event: event["start"]
    )

    return selected