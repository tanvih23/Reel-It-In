# Vantage

### A semantic video layer for live events — near-real-time safety alerts and auto-generated highlight reels, from a single drone feed.

> **Note:** "Vantage" is a working name. Swap globally before submission if you pick something else.

---

## The problem

Crowd-crush incidents at large events are almost always visible 60–120 seconds before they turn fatal — but nobody is watching that specific moment in hours of footage across multiple feeds. Meanwhile, colleges pay separately for post-event highlight editing. Two problems, one drone already flying overhead.

## What Vantage does

**One video source → two useful outputs off the same infrastructure:**

- **Safety** *(during the event)* — A live drone feed is chunked every 15 seconds and analyzed by [Reka Vision](https://reka.ai) with a set of natural-language safety questions ("is anyone tightly surrounded," "is the crowd suddenly bunching up," "is someone on the ground"). Matches surface on a monitor dashboard for a **human security lead** to act on. This is an attention aid, not an autonomous decision-maker.

- **Highlights** *(after the event)* — The same recorded footage is analyzed with a different question set ("crowd cheering," "confetti moment," "performer close-up under stage lights"), and matched timestamps are auto-cut and stitched into a highlight reel.

Same pipeline. Same "understanding." Two very different questions, two very different outputs.

## How it works

```
                        ┌──────────────────────┐
                        │  Drone / Video Source│
                        └──────────┬───────────┘
                                   │ RTMP stream
                                   ▼
                        ┌──────────────────────┐
                        │  Ingest + Chunker    │  15s .mp4 files
                        │  (FFmpeg)            │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
        ┌────────────────────┐         ┌────────────────────┐
        │ Safety Vision      │         │ Full-Video Store   │
        │ → Reka Vision API  │         │ (post-event only)  │
        │ → JSON events      │         └──────────┬─────────┘
        └──────────┬─────────┘                    │
                   │                              ▼
                   ▼                    ┌────────────────────┐
        ┌────────────────────┐          │ Highlight Pipeline │
        │ Alert Middleware   │          │ → Reka Vision API  │
        │ (threshold, dedup, │          │ → moviepy stitch   │
        │  prioritize)       │          └──────────┬─────────┘
        └──────────┬─────────┘                     │
                   │                               ▼
                   ▼                       ┌───────────────┐
        ┌────────────────────┐             │ highlights.mp4│
        │ Monitor Dashboard  │             └───────────────┘
        │ (Streamlit)        │
        └────────────────────┘
```

## Tech stack

- **Language:** Python 3.11+
- **Vision:** [Reka Vision API](https://docs.reka.ai) via `reka-api` SDK (OpenAI-compatible)
- **Video:** FFmpeg for chunking, moviepy for highlight stitching
- **Ingest:** Python `av` for RTMP receive (or nginx-rtmp as bridge)
- **Dashboard:** Streamlit
- **Deployment:** Docker + docker-compose
- **Storage:** SQLite for the event log (zero-config, deterministic replay)

## Setup

### Prerequisites

- Python 3.11 or newer
- FFmpeg installed and on your `PATH` ([download](https://ffmpeg.org/download.html))
- A Reka API key — sign up at [platform.reka.ai](https://platform.reka.ai) (new accounts get free evaluation credits)
- *(Optional)* A DJI drone with the DJI Fly app for live RTMP push, or any RTMP source

### Install

```bash
git clone https://github.com/<your-org>/vantage.git
cd vantage
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```
REKA_API_KEY=your_key_here
RTMP_INGEST_URL=rtmp://0.0.0.0:1935/live/stream
CHUNK_DIR=./data/chunks
EVENTS_DB=./data/events.db
CONFIDENCE_THRESHOLD=0.65
```

> **Never commit `.env`.** It's already in `.gitignore` — keep it that way.

### Run the demo (three terminals)

**Terminal 1 — start the ingest + chunker:**
```bash
python -m vantage.ingest --source path/to/sample_footage.mp4  # "fake live" playback
# OR
python -m vantage.ingest --source rtmp://your.drone.stream    # real live source
```

**Terminal 2 — start the vision worker + middleware:**
```bash
python -m vantage.vision.safety_worker
```

**Terminal 3 — start the dashboard:**
```bash
streamlit run vantage/dashboard/app.py
```

Then open [http://localhost:8501](http://localhost:8501) — alerts populate live as the video plays.

**Generate a highlight reel from recorded footage:**
```bash
python -m vantage.highlights --input path/to/full_footage.mp4 --output highlights.mp4
```

### One-command demo (bonus)

```bash
make demo         # spins up all three components + plays sample footage
```

## Project structure

```
vantage/
├── ingest/           # RTMP receiver + FFmpeg chunker
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

**Human-in-the-loop, always.** Every safety alert surfaces to a human monitor. Nothing auto-dispatches to police. Nothing triggers a public alarm. Vantage is one more pair of eyes that never gets tired — not a replacement for trained security personnel.

**No identity, ever.** No facial recognition. No biometric identification. No per-person tracking. Reka Vision receives short clips and returns semantic labels about aggregate behavior. Chunks are purged after analysis. By design, the system cannot output anything that identifies an individual.

**Understated, not overpromised.** Vantage does not "prevent stampedes." It helps a human notice concerning patterns 30 seconds sooner than they otherwise might. That's the honest claim — and it's the one that matters.

**Natural-language reconfiguration.** No retraining, no rule authoring, no engineer needed. A security lead types a new detection into the dashboard mid-event ("watch for anyone climbing the lighting rig") and the system starts checking for it on the next chunk.

## Evaluation

Precision/recall numbers for the safety question set, measured against a labeled test set of `N` clips, are in [`docs/eval-results.md`](docs/eval-results.md). Prompts are iterated against these numbers, not against gut feel.

## Team

- **[Name]** — Ingest & Drone Integration Lead
- **Tanvi** — Safety Vision Pipeline Lead
- **[Name]** — Highlights Vision + Video Assembly Lead
- **[Name]** — Alert Middleware, Eval Harness & Demo Infrastructure Lead

## Built for

**[Hackathon Name]** — Tracks: AIML · Multimedia Tech · Open Innovation

Sponsor track: Reka AI

## License

MIT — see [LICENSE](LICENSE).