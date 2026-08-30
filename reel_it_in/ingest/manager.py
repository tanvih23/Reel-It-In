"""Run one chunker per camera and keep them alive.

Reads the comma-separated CAMERA_SOURCES from .env, starts a chunker
subprocess for each, and restarts any that die. A phone that drops off the
wifi comes back on its own within a few seconds instead of staying dead.

Run:
    python -m reel_it_in.ingest.manager
    python -m reel_it_in.ingest.manager --sources 0,http://10.52.222.232:8080/video
"""

import argparse
import os
import subprocess
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RESTART_DELAY = 3.0     # seconds to wait before restarting a dead camera
POLL_SECONDS = 2.0      # how often to check whether processes are alive


def spawn(source: str, cam: str, seconds: int) -> subprocess.Popen:
    """Start one chunker as its own process."""
    cmd = [
        sys.executable, "-m", "reel_it_in.ingest",
        "--source", source,
        "--cam", cam,
        "--seconds", str(seconds),
    ]
    print(f"[manager] starting {cam} <- {source}", flush=True)
    return subprocess.Popen(cmd)


def main():
    ap = argparse.ArgumentParser(description="Run and supervise one chunker per camera.")
    ap.add_argument("--sources", default=os.getenv("CAMERA_SOURCES", ""),
                    help="comma-separated list of sources (overrides CAMERA_SOURCES)")
    ap.add_argument("--seconds", type=int, default=int(os.getenv("CHUNK_SECONDS", "15")))
    args = ap.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    if not sources:
        sys.exit("No sources. Set CAMERA_SOURCES in .env or pass --sources.")

    # cam ids are positional: first source is cam0, second cam1, and so on.
    # This is what keeps chunk filenames from colliding in the shared folder.
    cams = [(f"cam{i}", src) for i, src in enumerate(sources)]

    print(f"[manager] {len(cams)} camera(s), {args.seconds}s chunks", flush=True)

    procs = {cam: spawn(src, cam, args.seconds) for cam, src in cams}
    sources_by_cam = dict(cams)
    restarts = {cam: 0 for cam, _ in cams}

    try:
        while True:
            time.sleep(POLL_SECONDS)
            for cam, proc in list(procs.items()):
                if proc.poll() is None:
                    continue
                if proc.returncode == 0:
                    print(f"[manager] {cam} finished cleanly, not restarting", flush=True)
                    del procs[cam]
                    continue

                restarts[cam] += 1    # still running

                restarts[cam] += 1
                print(f"[manager] {cam} died (exit {proc.returncode}), "
                      f"restart #{restarts[cam]} in {RESTART_DELAY:.0f}s", flush=True)
                time.sleep(RESTART_DELAY)
                procs[cam] = spawn(sources_by_cam[cam], cam, args.seconds)

    except KeyboardInterrupt:
        print("\n[manager] stopping all cameras...", flush=True)

    finally:
        for cam, proc in procs.items():
            if proc.poll() is None:
                proc.terminate()
        for cam, proc in procs.items():
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("[manager] done.", flush=True)
        for cam, n in restarts.items():
            if n:
                print(f"[manager] {cam} restarted {n} time(s)", flush=True)


if __name__ == "__main__":
    main()