"""
Run Reka Vision highlight detection
and save the results to a JSON file.
"""

import json

from reel_it_in.vision.highlights import (
    upload_video,
    wait_until_indexed,
    find_highlights,
)


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

VIDEO_PATH = "data/samples/test.mp4"

OUTPUT_PATH = "data/samples/highlights.json"


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

def main():

    print("===================================")
    print("     REEL-IT-IN HIGHLIGHT DETECTOR")
    print("===================================")

    # ----------------------------------------------
    # STEP 1: Upload video to Reka
    # ----------------------------------------------

    video_id = upload_video(VIDEO_PATH)

    # ----------------------------------------------
    # STEP 2: Wait for Reka to finish indexing
    # ----------------------------------------------

    wait_until_indexed(video_id)

    # ----------------------------------------------
    # STEP 3: Ask Reka for highlight moments
    # ----------------------------------------------

    events = find_highlights(video_id)

    # ----------------------------------------------
    # STEP 4: Save results
    # ----------------------------------------------

    output = {
        "video": VIDEO_PATH,
        "video_id": video_id,
        "highlights": events,
    }

    with open(OUTPUT_PATH, "w") as file:
        json.dump(output, file, indent=4)

    # ----------------------------------------------
    # STEP 5: Print a summary
    # ----------------------------------------------

    print("\n===================================")
    print("       HIGHLIGHT DETECTION DONE")
    print("===================================")

    print(f"Total highlights found: {len(events)}")
    print(f"Results saved to: {OUTPUT_PATH}")

    # Print each detected highlight
    for number, event in enumerate(events, start=1):

        print(
            f"\nHighlight {number}: "
            f"{event['start']:.2f}s → "
            f"{event['end']:.2f}s"
        )

        print(
            f"Score: {event['score']:.3f}"
        )

        print(
            f"Reason: {event['reason']}"
        )


# --------------------------------------------------
# START PROGRAM
# --------------------------------------------------

if __name__ == "__main__":
    main()