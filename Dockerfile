FROM python:3.11-slim

# FFmpeg is required for chunking
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# TODO: pick the default entrypoint (ingest, worker, or dashboard)
