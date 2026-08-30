"""Entry point for the Highlight Reel pipeline."""

import argparse
import json
import os

def ask_orientation() -> bool:
    """Ask the user whether they want a vertical or horizontal reel."""

    print("\nChoose reel orientation:")
    print("  1. Vertical (9:16 — Instagram/Shorts)")
    print("  2. Horizontal (original aspect ratio)")

    while True:
        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            return True
        if choice == "2":
            return False

        print("Invalid choice, please enter 1 or 2.")


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

EVENT_TYPE_CHOICES = [
    "college_fest",
    "concert",
    "sports",
    "cultural",
    "lecture",
    "competition",
    "custom",
]


def ask_event_type():
    """Ask the user what kind of event this video is, returns (event_type, custom_queries)."""

    print("\nSelect event type:")
    for i, name in enumerate(EVENT_TYPE_CHOICES, start=1):
        print(f"  {i}. {name}")

    while True:
        choice = input(f"Enter 1-{len(EVENT_TYPE_CHOICES)}: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(EVENT_TYPE_CHOICES):
            event_type = EVENT_TYPE_CHOICES[int(choice) - 1]
            break

        print("Invalid choice.")

    if event_type == "custom":
        raw = input("Enter custom search phrases, separated by commas: ").strip()
        custom_queries = [q.strip() for q in raw.split(",") if q.strip()]
        return event_type, custom_queries

    return event_type, None

def run_pipeline(
    video_path,
    output_dir="output",
    max_highlights=8,
    min_gap=2.0,
    target_duration=30,
    order="chronological",
    add_transitions=True,
    transition_duration=0.5,
    music_path=None,
    music_volume=0.15,
    vertical=False,
    event_type="college_fest",
    custom_queries=None,
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
        video_id,
        event_type=event_type,
        custom_queries=custom_queries,
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
        music_path=music_path,
        music_volume=music_volume,
        vertical=vertical,
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
        default="random",
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
        "--music",
        default="data/samples/track.mp3",
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
    parser.add_argument(
        "--vertical",
        action="store_true",
        default=None,
    )

    parser.add_argument(
        "--event-type",
        choices=EVENT_TYPE_CHOICES,
        default=None,
    )

    parser.add_argument(
        "--custom-queries",
        default=None,
        help="Comma-separated search phrases, used only with --event-type custom",
    )

    args = parser.parse_args()
    vertical = args.vertical
    if vertical is None:
        vertical = ask_orientation()

    if args.event_type is None:
        event_type, custom_queries = ask_event_type()
    else:
        event_type = args.event_type
        custom_queries = (
            [q.strip() for q in args.custom_queries.split(",") if q.strip()]
            if args.custom_queries else None
        )

    run_pipeline(
        video_path=args.video_path,
        output_dir=args.output_dir,
        max_highlights=args.max_highlights,
        min_gap=args.min_gap,
        target_duration=args.duration,
        order=args.order,
        add_transitions=not args.no_transitions,
        transition_duration=args.transition_duration,
        music_path=args.music,
        music_volume=args.music_volume,
        vertical=vertical,
        event_type=event_type,
        custom_queries=custom_queries,
    )
    


if __name__ == "__main__":
    main()