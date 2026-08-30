"""Create the final highlight reel."""

import json
import os
import random

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx,
    afx,
)

def get_beat_times(music_path):
    """Return a sorted list of beat timestamps (seconds) from a music file."""

    import librosa

    y, sr = librosa.load(music_path)
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    return sorted(beat_times.tolist())


def snap_to_beat(time_value, beat_times):
    """Return the closest beat timestamp to time_value."""

    if not beat_times:
        return time_value

    return min(beat_times, key=lambda b: abs(b - time_value))

def add_zoom(clip, zoom_amount=0.06):
    """Slowly zoom in over the clip's duration for a dynamic feel."""

    def scale(t):
        return 1 + zoom_amount * (t / clip.duration)

    return clip.resized(scale).with_position("center")

def smart_shuffle(highlights):
    """Shuffle highlights, avoiding two clips with the same query type in a row."""

    import random as _random

    remaining = highlights.copy()
    _random.shuffle(remaining)

    result = []

    while remaining:

        # Find a candidate that doesn't match the last placed clip's query
        placed = False

        for i, candidate in enumerate(remaining):
            if not result or candidate.get("query") != result[-1].get("query"):
                result.append(remaining.pop(i))
                placed = True
                break

        # If every remaining clip matches the last one's query, place it anyway
        if not placed:
            result.append(remaining.pop(0))

    return result

def crop_vertical(clip, target_ratio=9 / 16):
    """Center-crop a clip to a vertical (e.g. 9:16) aspect ratio."""

    w, h = clip.w, clip.h
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Too wide — crop the sides
        new_w = int(h * target_ratio)
        x1 = (w - new_w) // 2
        return clip.cropped(x1=x1, x2=x1 + new_w)
    else:
        # Too tall — crop top/bottom
        new_h = int(w / target_ratio)
        y1 = (h - new_h) // 2
        return clip.cropped(y1=y1, y2=y1 + new_h)
    
def create_highlight_reel(
    video_path,
    highlights_path,
    output_path,
    order="chronological",
    add_transitions=True,
    transition_duration=0.5,
    music_path=None,
    music_volume=0.5,
    vertical=False,
):
    """Create the final edited highlight reel."""

    # -----------------------------
    # CHECK INPUTS
    # -----------------------------

    if not os.path.isfile(video_path):
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    if not os.path.isfile(highlights_path):
        raise FileNotFoundError(
            f"Highlights file not found: {highlights_path}"
        )

    # -----------------------------
    # LOAD HIGHLIGHTS
    # -----------------------------

    print("[Stitch] Reading highlight data...")

    with open(highlights_path, "r") as file:
        data = json.load(file)

    highlights = data.get("highlights", [])

    if not highlights:
        raise ValueError("No highlights found.")

    # -----------------------------
    # ARRANGE ORDER
    # -----------------------------

    if order == "chronological":

        highlights.sort(
            key=lambda h: float(h["start"])
        )

    elif order == "score":

        highlights.sort(
            key=lambda h: float(h.get("score", 0)),
            reverse=True,
        )

    elif order == "random":

        highlights = smart_shuffle(highlights)

    else:
        raise ValueError(
            f"Invalid order: {order}"
        )

    print(
        f"[Stitch] {len(highlights)} highlights | "
        f"Order: {order}"
    )

    # -----------------------------
    # OPEN SOURCE VIDEO
    # -----------------------------

    source = VideoFileClip(video_path)

    clips = []

    try:

        # -----------------------------
        # CREATE INDIVIDUAL CLIPS
        # -----------------------------
        beat_times = get_beat_times(music_path) if (music_path and os.path.isfile(music_path)) else None

        if beat_times:
            print(f"[Stitch] Detected {len(beat_times)} beats for cut-syncing.")
            
        for index, highlight in enumerate(
            highlights,
            start=1,
        ):

            start = max(
                0,
                float(highlight["start"])
            )

            end = min(
                source.duration,
                float(highlight["end"])
            )

            if beat_times:
                clip_duration = end - start
                snapped_start = snap_to_beat(start, beat_times)
                end = snapped_start + clip_duration
                start = snapped_start
                end = min(source.duration, end)


            if end <= start:
                print(
                    f"[Stitch] Skipping invalid "
                    f"highlight {index}"
                )
                continue

            print(
                f"[Stitch] Clip {index}: "
                f"{start:.2f}s → {end:.2f}s"
            )

            clip = source.subclipped(start, end)
            clip = clip.without_audio()
            clip = add_zoom(clip)
            if vertical:
                clip = crop_vertical(clip)

            # -------------------------
            # TRANSITION
            # -------------------------

            if (
                add_transitions
                and transition_duration > 0
            ):

                effects = []

                if index > 1:
                    effects.append(
                        vfx.CrossFadeIn(
                            transition_duration
                        )
                    )

                if index < len(highlights):
                    effects.append(
                        vfx.CrossFadeOut(
                            transition_duration
                        )
                    )

                if effects:
                    clip = clip.with_effects(
                        effects
                    )

            clips.append(clip)

        if not clips:
            raise ValueError(
                "No valid highlight clips created."
            )

        # -----------------------------
        # COMBINE CLIPS
        # -----------------------------

        print(
            f"[Stitch] Combining "
            f"{len(clips)} clips..."
        )

        padding = 0

        if (
            add_transitions
            and len(clips) > 1
        ):
            padding = -transition_duration

        final_video = concatenate_videoclips(
            clips,
            method="compose",
            padding=padding,
        )

        # -----------------------------
        # BACKGROUND MUSIC ONLY
        # -----------------------------

        if music_path:

            if not os.path.isfile(music_path):
                raise FileNotFoundError(
                    f"Music file not found: {music_path}"
                )

            print(f"[Stitch] Loading music: {music_path}")

            music = AudioFileClip(music_path)

            print(
                f"[Stitch] Music duration: "
                f"{music.duration:.2f}s"
            )

            # Repeat music if it is shorter than the reel
            music = music.with_effects([
                afx.AudioLoop(
                    duration=final_video.duration
                )
            ])

            # Set music volume
            music = music.with_effects([
                afx.MultiplyVolume(music_volume)
            ])

            # Make absolutely sure the original video
            # audio is NOT used.
            final_video = final_video.without_audio()

            # Attach ONLY the music
            final_video = final_video.with_audio(
                music.with_duration(final_video.duration)
            )

            print("[Stitch] Background music attached.")

        # -----------------------------
        # CREATE OUTPUT DIRECTORY
        # -----------------------------

        os.makedirs(
            os.path.dirname(output_path),
            exist_ok=True,
        )

        # -----------------------------
        # WRITE VIDEO
        # -----------------------------

        print(
            f"[Stitch] Creating: "
            f"{output_path}"
        )

        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=source.fps,
        )

        # -----------------------------
        # FINISHED
        # -----------------------------

        print()
        print(
            "================================"
        )
        print(
            "       HIGHLIGHT REEL READY"
        )
        print(
            "================================"
        )
        print(
            f"Output: {output_path}"
        )
        print(
            f"Duration: "
            f"{final_video.duration:.2f}s"
        )

        final_video.close()

    finally:

        for clip in clips:

            try:
                clip.close()
            except Exception:
                pass

        source.close()
