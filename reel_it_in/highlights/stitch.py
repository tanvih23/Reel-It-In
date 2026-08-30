"""Create the final highlight reel."""

import json
import os
import random

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    vfx,
    afx,
)

from .captions import overlay_text, suggest_post_caption


def add_caption(clip, text, font_path):
    """Add text at the bottom of the video."""

    if not text or not font_path:
        return clip

    if not os.path.isfile(font_path):
        print(f"[Stitch] Font not found: {font_path}")
        return clip

    try:
        text_clip = TextClip(
            font=font_path,
            text=text,
            font_size=28,
            color="white",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(clip.w - 80, None),
        )

        text_clip = (
            text_clip
            .with_duration(clip.duration)
            .with_position(("center", clip.h - text_clip.h - 50))
        )

        return CompositeVideoClip([clip, text_clip])

    except Exception as error:
        print(f"[Stitch] Caption skipped: {error}")
        return clip


def create_highlight_reel(
    video_path,
    highlights_path,
    output_path,
    order="chronological",
    add_transitions=True,
    transition_duration=0.5,
    add_captions=False,
    caption_font=None,
    music_path=None,
    music_volume=0.5,
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

            # -------------------------
            # CAPTION
            # -------------------------

            if add_captions:

                caption = overlay_text(
                    highlight
                )

                clip = add_caption(
                    clip,
                    caption,
                    caption_font,
                )

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
                afx.MultiplyVolume(0.7)
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
        # SOCIAL CAPTION
        # -----------------------------

        caption_path = (
            os.path.splitext(output_path)[0]
            + "_caption.txt"
        )

        with open(
            caption_path,
            "w",
        ) as file:

            file.write(
                suggest_post_caption(
                    highlights
                )
            )

        print(
            f"[Stitch] Social caption: "
            f"{caption_path}"
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
