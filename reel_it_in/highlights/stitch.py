"""Create a customizable highlight reel from selected timestamps."""

import json
import os
import random
#new branch
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


def _add_caption(clip, text: str, font_path):
    """Overlay a short caption at the bottom of a clip. Skips quietly if it fails."""

    if not text:
        return clip

    try:
        txt_clip = (
            TextClip(
                font=font_path,          # path to a .ttf file
                text=text,
                font_size=48,
                color="white",
                stroke_color="black",
                stroke_width=2,
                method="caption",
                size=(clip.w - 80, None),
            )
            .with_duration(clip.duration)
            .with_position(("center", "bottom"))
        )
        return CompositeVideoClip([clip, txt_clip])
    except Exception as error:
        print(f"[Stitch] Skipping caption (couldn't render text): {error}")
        return clip


def create_highlight_reel(
    video_path: str,
    highlights_path: str,
    output_path: str,
    order: str = "chronological",       # "chronological" | "score" | "random"
    add_transitions: bool = True,
    transition_duration: float = 0.5,
    add_captions: bool = False,
    caption_font=None,
    music_path=None,
    music_volume: float = 0.15,
    save_caption_suggestion: bool = True,
) -> None:
    """Cut and combine selected highlights into one customizable reel."""

    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if not os.path.isfile(highlights_path):
        raise FileNotFoundError(f"Highlights file not found: {highlights_path}")

    print("[Stitch] Reading highlight data...")
    with open(highlights_path, "r") as file:
        data = json.load(file)

    highlights = data.get("highlights", [])
    if not highlights:
        raise ValueError("No highlights were found in the JSON file.")

    # Arrange playback order
    if order == "chronological":
        highlights = sorted(highlights, key=lambda h: h["start"])
    elif order == "score":
        highlights = sorted(highlights, key=lambda h: h.get("score", 0), reverse=True)
    elif order == "random":
        highlights = highlights.copy()
        random.shuffle(highlights)
    else:
        raise ValueError(f"Unknown order: {order}")

    print(f"[Stitch] Found {len(highlights)} highlights. Order: {order}")
    print(f"[Stitch] Opening video: {video_path}")

    source = VideoFileClip(video_path)
    clips = []
    n = len(highlights)

    for i, highlight in enumerate(highlights, start=1):

        start = max(0, float(highlight["start"]))
        end = min(source.duration, float(highlight["end"]))

        print(f"[Stitch] Highlight {i}: {start:.2f}s → {end:.2f}s")

        if end <= start:
            print(f"[Stitch] Skipping highlight {i}: invalid timestamps.")
            continue

        clip = source.subclipped(start, end)

        if clip.audio is not None:
            clip = clip.with_audio(clip.audio.with_duration(clip.duration))

        if add_captions:
            clip = _add_caption(clip, overlay_text(highlight), caption_font)

        if add_transitions and n > 1:
            effects = []
            if i > 1:
                effects.append(vfx.CrossFadeIn(transition_duration))
            if i < n:
                effects.append(vfx.CrossFadeOut(transition_duration))
            if effects:
                clip = clip.with_effects(effects)

        clips.append(clip)

    if not clips:
        source.close()
        raise ValueError("No valid highlight clips could be created.")

    print(f"[Stitch] Combining {len(clips)} clips...")

    padding = -transition_duration if (add_transitions and len(clips) > 1) else 0

    final_video = concatenate_videoclips(clips, method="compose", padding=padding)

    if final_video.audio is not None:
        final_video = final_video.with_audio(
            final_video.audio.with_duration(final_video.duration)
        )

    if music_path:
        if not os.path.isfile(music_path):
            print(f"[Stitch] Music file not found, skipping: {music_path}")
        else:
            print(f"[Stitch] Adding background music: {music_path}")

            music = (
                AudioFileClip(music_path)
                .with_effects([
                    afx.AudioLoop(duration=final_video.duration),
                    afx.MultiplyVolume(music_volume),
                ])
                .with_duration(final_video.duration)
            )

            mixed_audio = (
                CompositeAudioClip([final_video.audio, music])
                if final_video.audio is not None
                else music
            )
            final_video = final_video.with_audio(mixed_audio)

    output_directory = os.path.dirname(output_path)
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    print(f"[Stitch] Creating highlight reel: {output_path}")

    final_video.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=source.fps,
    )

    final_duration = final_video.duration

    if save_caption_suggestion:
        caption_path = os.path.splitext(output_path)[0] + "_caption.txt"
        with open(caption_path, "w") as f:
            f.write(suggest_post_caption(highlights))
        print(f"[Stitch] Suggested social caption saved to: {caption_path}")

    final_video.close()
    for clip in clips:
        clip.close()
    source.close()

    print()
    print("===================================")
    print("       HIGHLIGHT REEL CREATED")
    print("===================================")
    print(f"Output: {output_path}")
    print(f"Duration: {final_duration:.2f} seconds")