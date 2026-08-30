"""FFmpeg chunker - cuts the incoming feed into 15s .mp4 files in CHUNK_DIR.

Chunks are written to a staging folder first and only moved into CHUNK_DIR once
complete, so the vision worker never picks up a half-written file.

Run:
    python -m reel_it_in.ingest --source data/sample/crowd.mp4 --loop
    python -m reel_it_in.ingest --source 0
    python -m reel_it_in.ingest --source http://192.168.1.15:8080/video --cam cam1
"""

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from .sources import describe, input_args

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def build_cmd(source, out_pattern, seconds, loop, force_reencode):
    args, must_reencode = input_args(source, loop)

    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y"] + args

    if must_reencode or force_reencode:
        cmd += [
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-r", "15",   # fixed fps - flow metrics are per-frame, must be constant
            "-g", "30",
            "-an",
        ]
    else:
        cmd += ["-c", "copy"]   # fast and lossless, but cuts only on keyframes

    cmd += [
        "-f", "segment",
        "-segment_time", str(seconds),
        "-segment_format", "mp4",
        "-reset_timestamps", "1",
        out_pattern,
    ]
    return cmd


def publisher(staging: Path, out: Path, stop: threading.Event):
    """Move completed chunks from staging into the shared chunk folder.

    A chunk is finished once the NEXT one has appeared, so the newest file is
    always left alone. os.replace is atomic within a filesystem, so anything
    visible in `out` is guaranteed complete.
    """
    while not stop.is_set():
        files = sorted(staging.glob("*.mp4"))
        for f in files[:-1]:
            try:
                os.replace(f, out / f.name)
                print(f"[chunk] {f.name}", flush=True)
            except OSError as e:
                print(f"[warn] could not publish {f.name}: {e}", flush=True)
        time.sleep(0.5)

        # FFmpeg has stopped, so the last file is finished too.
    for f in sorted(staging.glob("*.mp4")):
        try:
            if f.stat().st_size < 10_000:   # header-only stub from an interrupt
                f.unlink()
                continue
            os.replace(f, out / f.name)
            print(f"[chunk] {f.name} (final)", flush=True)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description="Chunk one video source into N-second mp4 files.")
    ap.add_argument("--source", default=os.getenv("CAMERA_SOURCES", "data/sample/crowd.mp4"))
    ap.add_argument("--cam", default="cam0", help="short id, used as the chunk filename prefix")
    ap.add_argument("--out", default=os.getenv("CHUNK_DIR", "./data/chunks"))
    ap.add_argument("--staging", default=os.getenv("STAGING_DIR", "./data/staging"))
    ap.add_argument("--seconds", type=int, default=int(os.getenv("CHUNK_SECONDS", "15")))
    ap.add_argument("--loop", action="store_true", help="loop a file source forever")
    ap.add_argument("--no-reencode", action="store_true",help="stream-copy instead of re-encoding (faster, but chunk lengths vary)")
    args = ap.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg not found on PATH. Install it: https://ffmpeg.org/download.html")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    staging = Path(args.staging) / args.cam
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    pattern = str(staging / f"{args.cam}_%04d.mp4")
    cmd = build_cmd(args.source, pattern, args.seconds, args.loop, not args.no_reencode)

    print(f"[ingest] {args.cam}: {describe(args.source)} source '{args.source}', "
          f"{args.seconds}s chunks -> {out}")
    print("[ingest]", " ".join(cmd), flush=True)

    stop = threading.Event()
    pub = threading.Thread(target=publisher, args=(staging, out, stop), daemon=True)
    pub.start()

    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n[ingest] stopping...", flush=True)
        proc.terminate()
        proc.wait()
    finally:
        stop.set()
        pub.join(timeout=5)
        print("[ingest] done.", flush=True)