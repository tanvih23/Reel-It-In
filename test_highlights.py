from reel_it_in.vision.highlights import (
upload_video,
wait_until_indexed,
find_highlights,
)

VIDEO_PATH = "data/samples/test.mp4"

print("===================================")
print("     REEL-IT-IN HIGHLIGHT TEST")
print("===================================")

# Step 1: Upload the video

video_id = upload_video(VIDEO_PATH)

# Step 2: Wait for Reka to finish indexing

wait_until_indexed(video_id)

# Step 3: Search for exciting moments

events = find_highlights(video_id)

# Step 4: Print the results

print("\n===================================")
print("          HIGHLIGHT RESULTS")
print("===================================")

if not events:
    print("No highlight moments found.")

else:
    for number, event in enumerate(events, start=1):
        print(f"\nHighlight #{number}")
        print(f"Start:  {event['start']:.2f} seconds")
        print(f"End:    {event['end']:.2f} seconds")
        print(f"Score:  {event['score']:.3f}")
        print(f"Query:  {event['query']}")
        print(f"Reason: {event['reason']}")