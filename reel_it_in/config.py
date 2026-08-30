"""Loads settings from .env — see .env.example for the full key list."""

# TODO: read REKA_API_KEY, RTMP_INGEST_URL, CHUNK_DIR, EVENTS_DB,
# TODO: CONFIDENCE_THRESHOLD and expose them to the rest of the package
import os
from dotenv import load_dotenv

load_dotenv()

REKA_API_KEY = os.getenv("REKA_API_KEY")
CHUNK_DIR = os.getenv("CHUNK_DIR")
EVENTS_DB = os.getenv("EVENTS_DB")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.65))
CHUNK_SECONDS = int(os.getenv("CHUNK_SECONDS", 15))
STAGING_DIR = os.getenv("STAGING_DIR", "./data/staging")
CAMERA_SOURCES = os.getenv("CAMERA_SOURCES", "cam0")
WEBCAM_NAME = os.getenv("WEBCAM_NAME", "default")
FLOW_ENABLED = os.getenv("FLOW_ENABLED", "true").lower() == "true"
FLOW_COHERENCE_TURBULENT = float(os.getenv("FLOW_COHERENCE_TURBULENT", 0.6))
FLOW_MIN_OCCUPANCY = float(os.getenv("FLOW_MIN_OCCUPANCY", 0.3))
print("Loaded threshold:", CONFIDENCE_THRESHOLD)
if REKA_API_KEY:
    print("Key loaded:", REKA_API_KEY[:8], "...")
else:
    print("WARNING: REKA_API_KEY not found — check that .env exists and is filled in.")