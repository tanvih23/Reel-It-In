import json

from reel_it_in.highlights.selection import select_highlights


INPUT_PATH = "data/samples/highlights.json"
OUTPUT_PATH = "data/samples/selected_highlights.json"


print("===================================")
print("   SELECTING FINAL HIGHLIGHTS")
print("===================================")


# 1. Read Reka's results
print("[Selection] Reading Reka results...")

with open(INPUT_PATH, "r") as file:
    data = json.load(file)


events = data.get("highlights", [])

print(
    f"[Selection] Reka returned "
    f"{len(events)} candidate highlights."
)


# 2. Select the best non-overlapping highlights
selected = select_highlights(
    events,
    max_highlights=3,
)


print(
    f"[Selection] Selected "
    f"{len(selected)} highlights."
)


# 3. Create output data
output_data = {
    "video": data.get("video"),
    "video_id": data.get("video_id"),
    "highlights": selected,
}


# 4. Save selected highlights
with open(OUTPUT_PATH, "w") as file:
    json.dump(
        output_data,
        file,
        indent=4,
    )


print()
print("===================================")
print("   SELECTION COMPLETE")
print("===================================")

print(f"Saved to: {OUTPUT_PATH}")

for i, highlight in enumerate(selected, start=1):

    print()
    print(f"Highlight {i}")
    print(
        f"  Time: "
        f"{highlight['start']:.2f}s → "
        f"{highlight['end']:.2f}s"
    )
    print(
        f"  Score: "
        f"{highlight['score']:.3f}"
    )
    print(
        f"  Reason: "
        f"{highlight['reason']}"
    )