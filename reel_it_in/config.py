"""Loads settings from .env — see .env.example for the full key list."""

# TODO: read REKA_API_KEY, RTMP_INGEST_URL, CHUNK_DIR, EVENTS_DB,
# TODO: CONFIDENCE_THRESHOLD and expose them to the rest of the package
import os
from dotenv import load_dotenv

load_dotenv()

REKA_API_KEY = os.getenv("REKA_API_KEY")
RTMP_INGEST_URL = os.getenv("RTMP_INGEST_URL")
CHUNK_DIR = os.getenv("CHUNK_DIR")
EVENTS_DB = os.getenv("EVENTS_DB")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.65))
print("Loaded threshold:", CONFIDENCE_THRESHOLD)
print("Key loaded:", REKA_API_KEY[:8], "...")