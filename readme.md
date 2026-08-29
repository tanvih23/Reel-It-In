# Reel-It-In

### A semantic video layer for live events — near-real-time safety alerts and auto-generated highlight reels, from any camera source.

> **Note:** "Reel-It-In" is a working name. Swap globally before submission if you pick something else.

---

## The problem

Crowd-crush incidents at large events are almost always visible 60–120 seconds before they turn fatal — but nobody is watching that specific moment across dozens of camera feeds from volunteer phones and CCTV. Meanwhile, colleges pay separately for post-event highlight editing. Two problems, same cameras already rolling.

## What Reel-It-In does

**Any number of camera sources → two useful outputs off the same infrastructure:**

- **Safety** *(during the event)* — Live video from phone cameras, webcams, or CCTV is chunked every 15 seconds and analyzed by [Reka Vision](https://reka.ai) with a set of natural-language safety questions ("is anyone tightly surrounded," "is the crowd suddenly bunching up," "is someone on the ground"). Matches surface on a monitor dashboard for a **human security lead** to act on. This is an attention aid, not an autonomous decision-maker.

- **Highlights** *(after the event)* — The same recorded footage is analyzed with a different question set ("crowd cheering," "confetti moment," "performer close-up under stage lights"), and matched timestamps are auto-cut and stitched into a highlight reel.

Same pipeline. Same "understanding." Two very different questions, two very different outputs.

## How it works

```
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ Phone 1 │  │ Phone 2 │  │ Webcam  │  ← any HTTP video source
  └────┬────┘  └────┬────┘  └────┬────┘
       │            │            │
       └────────────┼────────────┘
                    ▼
         ┌──────────────────────┐
         │  Ingest Server       │  receives streams via HTTP / IP Webcam
         │  + FFmpeg Chunker    │  outputs 15s .mp4 files per source
         └──────────┬───────────┘
                    │
     ┌──────────────┴──────────────┐
     ▼                             ▼
 ┌────────────────────┐  ┌────────────────────┐
 │ Safety Vision      │  │ Full-Video Store   │
 │ → Reka Vision API  │  │ (post-event only)  │
 │ → JSON events      │  └──────────┬─────────┘
 └──────────┬─────────┘             │
            │                       ▼
            ▼             ┌────────────────────┐
 ┌────────────────────┐   │ Highlight Pipeline │
 │ Alert Middleware   │   │ → Reka Vision API  │
 │ (threshold, dedup, │   │ → moviepy stitch   │
 │  prioritize)       │   └──────────┬─────────┘
 └──────────┬─────────┘              │
            │                        ▼
            ▼                ┌───────────────┐
 ┌────────────────────┐      │ highlights.mp4│
 │ Monitor Dashboard  │      └───────────────┘
 │ (Streamlit)        │
 └────────────────────┘
```

## Tech stack

- **Language:** Python 3.11+
- **Vision:** [Reka Vision API](https://docs.reka.ai) via `reka-api` SDK (OpenAI-compatible)
- **Video:** FFmpeg for chunking, moviepy for highlight stitching
- **Ingest:** Flask server accepting HTTP video streams from phone cameras (via [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) or browser-based capture), laptop webcams, or any IP camera
- **Dashboard:** Streamlit
- **Deployment:** Docker + docker-compose
- **Storage:** SQLite for the event log (zero-config, deterministic replay)

## Setup

### Prerequisites

- Python 3.11 or newer
- FFmpeg installed and on your `PATH` ([download](https://ffmpeg.org/download.html))
- A Reka API key — sign up at [platform.reka.ai](https://platform.reka.ai) (new accounts get free evaluation credits)
- *(For live demo)* Any Android phone with [IP Webcam](https://play.google.com/store/apps/details?id=com.pas.webcam) installed, or a laptop with a webcam — both the phone and laptop must be on the same wifi network

### Install

```bash
git clone https://github.com/tanvih23/reel-it-in.git
cd reel-it-in
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```
REKA_API_KEY=your_key_here
INGEST_PORT=5001
CAMERA_SOURCES=http://192.168.1.15:8080/video,http://192.168.1.22:8080/video
CHUNK_DIR=./data/chunks
EVENTS_DB=./data/events.db
CONFIDENCE_THRESHOLD=0.65
```

> **Never commit `.env`.** It's already in `.gitignore` — keep it that way.

### Run the demo (three terminals)

**Terminal 1 — start the ingest + chunker:**
```bash
python -m reel-it-in.ingest --source path/to/sample_footage.mp4              # pre-recorded playback
# OR
python -m reel-it-in.ingest --source http://192.168.1.15:8080/video          # phone via IP Webcam
# OR
python -m reel-it-in.ingest --source 0                                        # laptop webcam (device 0)
```

**Terminal 2 — start the vision worker + middleware:**
```bash
python -m reel-it-in.vision.safety_worker
```

**Terminal 3 — start the dashboard:**
```bash
streamlit run reel-it-in/dashboard/app.py
```

Then open [http://localhost:8501](http://localhost:8501) — alerts populate live as the video plays.

**Generate a highlight reel from recorded footage:**
```bash
python -m reel-it-in.highlights --input path/to/full_footage.mp4 --output highlights.mp4
```

### One-command demo (bonus)

```bash
make demo         # spins up all three components + plays sample footage
```

## Project structure

```
reel-it-in/
├── ingest/           # HTTP/webcam receiver + FFmpeg chunker
├── vision/
│   ├── safety.py     # safety question set + Reka caller
│   └── highlights.py # highlight question set + Reka caller
├── middleware/       # thresholding, dedup, prioritization, feed-loss detection
├── dashboard/        # Streamlit monitor UI
├── highlights/       # moviepy stitching + reel assembly
├── eval/             # labeled test clips + precision/recall harness
├── data/             # chunks, events DB, sample footage (gitignored)
└── docs/             # architecture notes, prompt sets, demo script
```

## Design principles

**Human-in-the-loop, always.** Every safety alert surfaces to a human monitor. Nothing auto-dispatches to police. Nothing triggers a public alarm. Reel-It-In is one more pair of eyes that never gets tired — not a replacement for trained security personnel.

**No identity, ever.** No facial recognition. No biometric identification. No per-person tracking. Reka Vision receives short clips and returns semantic labels about aggregate behavior. Chunks are purged after analysis. By design, the system cannot output anything that identifies an individual.

**Understated, not overpromised.** Reel-It-In does not "prevent stampedes." It helps a human notice concerning patterns 30 seconds sooner than they otherwise might. That's the honest claim — and it's the one that matters.

**Natural-language reconfiguration.** No retraining, no rule authoring, no engineer needed. A security lead types a new detection into the dashboard mid-event ("watch for anyone climbing the lighting rig") and the system starts checking for it on the next chunk.

## Evaluation

Precision/recall numbers for the safety question set, measured against a labeled test set of `N` clips, are in [`docs/eval-results.md`](docs/eval-results.md). Prompts are iterated against these numbers, not against gut feel.

## Team

- **Shambhavi Srivastava** — Ingest & Multi-Camera Lead
- **Tanvi Hanish** — Safety Vision Pipeline Lead
- **Vedita Jayswal** — Highlights Vision + Video Assembly Lead
- **Kirtika Agrawal** — Alert Middleware, Eval Harness & Demo Infrastructure Lead

## Built for

**DevJams'26** — Tracks: AIML · Multimedia Tech · Open Innovation

Sponsor track: Reka AI

## License

MIT — see [LICENSE](LICENSE).