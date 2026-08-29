import json

from reel_it_in.highlights.stitch import create_highlight_reel


VIDEO_PATH = "data/samples/test.mp4"
HIGHLIGHTS_PATH = "data/samples/selected_highlights.json"
OUTPUT_PATH = "data/samples/selected_highlight_reel.mp4"


print("===================================")
print("     HIGHLIGHT STITCHING TEST")
print("===================================")


# Check that the selected highlights file exists
with open(HIGHLIGHTS_PATH, "r") as f:
    data = json.load(f)


print(f"Selected highlights: {len(data['highlights'])}")


for i, highlight in enumerate(data["highlights"], start=1):
    print(
        f"Highlight {i}: "
        f"{highlight['start']:.2f}s → "
        f"{highlight['end']:.2f}s"
    )


# Create the final reel
create_highlight_reel(
    video_path=VIDEO_PATH,
    highlights_path=HIGHLIGHTS_PATH,
    output_path=OUTPUT_PATH,
)


print()
print("===================================")
print("       FINAL REEL CREATED")
print("===================================")
print(f"Output: {OUTPUT_PATH}")