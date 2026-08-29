"""Entry point for the Highlight AI + Video Editor module."""

import argparse
import json
import os

from reel_it_in.vision.highlights import (
    upload_video,
    wait_until_indexed,
    find_highlights,
)
from reel_it_in.highlights.selection import select_highlights
from reel_it_in.highlights.stitch import create_highlight_reel


def run_pipeline(
    video_path: str,
    output_dir: str = "output",
    max_highlights: int = 8,
    min_gap: float = 2.0,
    target_duration: float = 30.0,
    order: str = "chronological",
    add_transitions: bool = True,
    transition_duration: float = 0.5,
    add_captions: bool = False,
    caption_font=None,
    music_path=None,
    music_volume: float = 0.15,
) -> None:
    video_id = upload_video(video_path)
    wait_until_indexed(video_id)
    raw_events = find_highlights(video_id)

    if not raw_events:
        print("[Main] Reka didn't find any highlights. Stopping.")
        return

    print(f"[Main] Reka returned {len(raw_events)} raw candidate moments.")

    selected = select_highlights(
        raw_events,
        max_highlights=max_highlights,
        min_gap=min_gap,
        target_duration=target_duration,
    )

    if not selected:
        print("[Main] Nothing survived the selection step. Stopping.")
        return

    print(f"[Main] Selected {len(selected)} final highlights.")

    os.makedirs(output_dir, exist_ok=True)
    highlights_json_path = os.path.join(output_dir, "highlights.json")

    with open(highlights_json_path, "w") as f:
        json.dump({"highlights": selected}, f, indent=2)

    reel_output_path = os.path.join(output_dir, "highlight_reel.mp4")

    create_highlight_reel(
        video_path=video_path,
        highlights_path=highlights_json_path,
        output_path=reel_output_path,
        order=order,
        add_transitions=add_transitions,
        transition_duration=transition_duration,
        add_captions=add_captions,
        caption_font=caption_font,
        music_path=music_path,
        music_volume=music_volume,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn a video into a highlight reel.")
    parser.add_argument("video_path")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--max-highlights", type=int, default=8)
    parser.add_argument("--min-gap", type=float, default=2.0)
    parser.add_argument("--duration", type=int, choices=[15, 30, 60], default=30)
    parser.add_argument("--order", choices=["chronological", "score", "random"], default="chronological")
    parser.add_argument("--no-transitions", action="store_true")
    parser.add_argument("--transition-duration", type=float, default=0.5)
    parser.add_argument("--captions", action="store_true")
    parser.add_argument("--caption-font", default=None)
    parser.add_argument("--music", default=None)
    parser.add_argument("--music-volume", type=float, default=0.15)

    args = parser.parse_args()

    run_pipeline(
        video_path=args.video_path,
        output_dir=args.output_dir,
        max_highlights=args.max_highlights,
        min_gap=args.min_gap,
        target_duration=float(args.duration),
        order=args.order,
        add_transitions=not args.no_transitions,
        transition_duration=args.transition_duration,
        add_captions=args.captions,
        caption_font=args.caption_font,
        music_path=args.music,
        music_volume=args.music_volume,
    )


if __name__ == "__main__":
    main()