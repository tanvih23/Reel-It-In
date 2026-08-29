"""Resolve a source string into FFmpeg input arguments.

Three kinds of source, one interface:
    "data/sample/crowd.mp4"              -> a file, paced to real speed
    "0"                                  -> a webcam attached to this machine
    "http://192.168.1.15:8080/video"     -> a phone running IP Webcam, or any stream
"""

import os
import platform
from pathlib import Path


def describe(source: str) -> str:
    """Classify a source string. Used for logging and for choosing input args."""
    if Path(source).exists():
        return "file"
    if source.isdigit():
        return "webcam"
    return "stream"


def _webcam_args(index: str) -> list[str]:
    """Webcam capture syntax differs per operating system."""
    system = platform.system()

    if system == "Windows":
        # DirectShow needs the device's actual name, not an index. Find yours with:
        #   ffmpeg -list_devices true -f dshow -i dummy
        # then put it in .env as WEBCAM_NAME=...
        name = os.getenv("WEBCAM_NAME", "Integrated Camera")
        return ["-f", "dshow", "-i", f"video={name}"]

    if system == "Darwin":
        return ["-f", "avfoundation", "-framerate", "30", "-i", index]

    return ["-f", "v4l2", "-i", f"/dev/video{index}"]


def input_args(source: str, loop: bool = False) -> tuple[list[str], bool]:
    """Return (ffmpeg input arguments, whether the stream must be re-encoded).

    Re-encoding is forced for webcams (raw frames have no container) and for
    network streams (IP Webcam sends MJPEG, which does not copy cleanly into mp4).
    Files can usually be stream-copied, which is much faster.
    """
    kind = describe(source)

    if kind == "file":
        args: list[str] = []
        if loop:
            args += ["-stream_loop", "-1"]
        # -re paces playback at real speed so a recording behaves like a live camera.
        # Without it FFmpeg races through the file and dumps every chunk at once.
        args += ["-re", "-i", source]
        return args, False

    if kind == "webcam":
        return _webcam_args(source), True

    return ["-i", source], True