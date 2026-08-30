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

def add_zoom(clip, zoom_amount=0.06):
    """Slowly zoom in over the clip's duration for a dynamic feel."""

    def scale(t):
        return 1 + zoom_amount * (t / clip.duration)

    return clip.resized(scale).with_position("center")

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

        random.shuffle(highlights)

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
