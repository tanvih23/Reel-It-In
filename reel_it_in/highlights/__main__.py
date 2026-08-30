"""Entry point for the Highlight Reel pipeline."""

import argparse
import json
import os

from reel_it_in.vision.highlights import (
    upload_video,
    wait_until_indexed,
    find_highlights,
)

from reel_it_in.highlights.selection import (
    select_highlights,
)

from reel_it_in.highlights.stitch import (
    create_highlight_reel,
)


def run_pipeline(
    video_path,
    output_dir="output",
    max_highlights=8,
    min_gap=2.0,
    target_duration=30,
    order="chronological",
    add_transitions=True,
    transition_duration=0.5,
    add_captions=False,
    caption_font=None,
    music_path=None,
    music_volume=0.15,
):

    # -----------------------------
    # 1. SEND VIDEO TO REKA
    # -----------------------------

    print("[Main] Uploading video...")

    video_id = upload_video(
        video_path
    )

    # -----------------------------
    # 2. WAIT FOR REKA
    # -----------------------------

    print("[Main] Waiting for indexing...")

    wait_until_indexed(
        video_id
    )

    # -----------------------------
    # 3. FIND HIGHLIGHTS
    # -----------------------------

    print("[Main] Finding highlights...")

    raw_events = find_highlights(
        video_id
    )

    if not raw_events:

        print(
            "[Main] No highlights found."
        )

        return

    print(
        f"[Main] Reka found "
        f"{len(raw_events)} candidates."
    )

    # -----------------------------
    # 4. SELECT BEST HIGHLIGHTS
    # -----------------------------

    selected = select_highlights(
        raw_events,
        max_highlights=max_highlights,
        min_gap=min_gap,
        target_duration=target_duration,
    )

    if not selected:

        print(
            "[Main] No highlights "
            "survived selection."
        )

        return

    print(
        f"[Main] Selected "
        f"{len(selected)} highlights."
    )

    # -----------------------------
    # 5. CREATE OUTPUT DIRECTORY
    # -----------------------------

    os.makedirs(
        output_dir,
        exist_ok=True,
    )

    # -----------------------------
    # 6. SAVE HIGHLIGHT DATA
    # -----------------------------

    highlights_path = os.path.join(
        output_dir,
        "highlights.json",
    )

    with open(
        highlights_path,
        "w",
    ) as file:

        json.dump(
            {
                "highlights": selected
            },
            file,
            indent=2,
        )

    # -----------------------------
    # 7. FINAL VIDEO PATH
    # -----------------------------

    output_path = os.path.join(
        output_dir,
        "highlight_reel.mp4",
    )

    # -----------------------------
    # 8. EDIT THE REEL
    # -----------------------------

    create_highlight_reel(
        video_path=video_path,
        highlights_path=highlights_path,
        output_path=output_path,
        order=order,
        add_transitions=add_transitions,
        transition_duration=transition_duration,
        add_captions=add_captions,
        caption_font=caption_font,
        music_path=music_path,
        music_volume=music_volume,
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Create an AI highlight reel."
        )
    )

    parser.add_argument(
        "video_path"
    )

    parser.add_argument(
        "--duration",
        type=int,
        choices=[15, 30, 60],
        default=30,
    )

    parser.add_argument(
        "--order",
        choices=[
            "chronological",
            "score",
            "random",
        ],
        default="chronological",
    )

    parser.add_argument(
        "--max-highlights",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--min-gap",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--no-transitions",
        action="store_true",
    )

    parser.add_argument(
        "--transition-duration",
        type=float,
        default=0.5,
    )

    parser.add_argument(
        "--captions",
        action="store_true",
    )

    parser.add_argument(
        "--caption-font",
        default="assets/fonts/Roboto-Bold.ttf",
    )

    parser.add_argument(
        "--music",
        default="data/music/track.mp3",
    )

    parser.add_argument(
        "--music-volume",
        type=float,
        default=0.5,
    )

    parser.add_argument(
        "--output-dir",
        default="output",
    )

    args = parser.parse_args()

    run_pipeline(
        video_path=args.video_path,
        output_dir=args.output_dir,
        max_highlights=args.max_highlights,
        min_gap=args.min_gap,
        target_duration=args.duration,
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