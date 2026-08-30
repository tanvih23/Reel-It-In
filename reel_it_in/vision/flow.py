"""Crowd-motion physics from dense optical flow. Owner: Tanvi.

This is our own detector — no API call, no model download, runs locally on
every chunk for free.

Grounded in Helbing, Johansson & Zein Al-Abideen, "The Dynamics of Crowd
Disasters: An Empirical Study", Phys. Rev. E 75, 046109 (2007). Their video
analysis of the 2006 Jamarat Bridge disaster found crowds pass through three
phases before a crush:

    LAMINAR      everyone moving smoothly in roughly one direction
    STOP_AND_GO  movement pulses through the crowd in waves
    TURBULENT    chaotic multi-directional displacement — the precursor to
                 lethal compression

Deaths began roughly 10 minutes after turbulence onset. Density alone does
not predict a crush; a dense but calm crowd is safe. What we measure here is
the *character* of the motion, not how many people are present.

We never detect, identify or track individuals — this operates on the raw
motion field of the whole frame, which is also why it costs nothing and
carries no privacy burden.
"""

import time

import cv2
import numpy as np

# --- Tunables -------------------------------------------------------------
# IMPORTANT: these are STARTING VALUES, not calibrated ones. They were sanity-
# checked against synthetic motion, not real crowd footage. Tune them against
# your own labelled clips before trusting any of them, and say they're
# untuned if asked.

TARGET_WIDTH = 480       # downscale before flow; Farneback is O(pixels)
FRAME_STRIDE = 2         # compare every Nth frame — bigger stride, more motion
MIN_MOTION_MAG = 0.35    # px/frame below this is sensor noise, not movement

MOVING_MIN_MAG = 0.60    # below this mean magnitude the scene is ~static
MIN_OCCUPANCY = 0.15     # below this the scene isn't a moving crowd (see note)
COHERENCE_LAMINAR = 0.55 # resultant length above this = one dominant direction
COHERENCE_TURBULENT = 0.30  # below this = directions scattered -> turbulent
PULSE_CV_THRESHOLD = 0.45   # temporal speed variation that reads as stop-and-go

# Why MIN_OCCUPANCY exists — this is a real false-positive mode we hit in
# testing, worth knowing about. On a near-empty scene the only "motion" is
# sensor noise, and noise points in random directions, so coherence collapses
# and the scene looks textbook turbulent. A quiet camera would then alert
# continuously. Turbulence is a BULK phenomenon: it needs a substantial part
# of the frame actually in motion, not a scattering of noisy pixels. So we
# require both disorder and occupancy before calling turbulence.

# Farneback parameters — defaults from the OpenCV docs, adequate for crowds.
FARNEBACK = dict(
    pyr_scale=0.5, levels=3, winsize=15,
    iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
)

PHASES = ("STATIC", "LAMINAR", "STOP_AND_GO", "TURBULENT")


def _iter_gray_frames(clip_path, target_width=TARGET_WIDTH, stride=FRAME_STRIDE):
    """Yield downscaled grayscale frames, every `stride`-th frame."""
    cap = cv2.VideoCapture(str(clip_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {clip_path}")

    idx = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride == 0:
                h, w = frame.shape[:2]
                if w > target_width:
                    scale = target_width / w
                    frame = cv2.resize(frame, (target_width, int(h * scale)))
                yield cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            idx += 1
    finally:
        cap.release()


def _pair_metrics(prev_gray, next_gray, compensate_camera_motion):
    """Metrics for one consecutive frame pair."""
    flow = cv2.calcOpticalFlowFarneback(prev_gray, next_gray, None, **FARNEBACK)

    if compensate_camera_motion:
        # A handheld phone pans and shakes, which shows up as the whole frame
        # drifting one way — indistinguishable from a crowd all walking one
        # way. Subtracting the median vector removes that global component.
        #
        # TRADE-OFF, and it matters: this also removes genuine uniform crowd
        # movement, so real laminar flow will read as weaker/noisier. Set this
        # False whenever the camera is actually mounted or on a tripod.
        flow = flow - np.median(flow.reshape(-1, 2), axis=0)

    dx, dy = flow[..., 0], flow[..., 1]
    magnitude = np.sqrt(dx * dx + dy * dy)

    moving = magnitude > MIN_MOTION_MAG
    occupancy = float(moving.mean())  # fraction of frame in motion

    if occupancy < 0.01:
        return {
            "mean_magnitude": float(magnitude.mean()),
            "coherence": 1.0,      # nothing moving -> no disorder to report
            "speed_dispersion": 0.0,
            "occupancy": occupancy,
        }

    mag_moving = magnitude[moving]

    # Directional coherence via the resultant-vector ratio:
    #     R = |sum(v)| / sum(|v|)      in [0, 1]
    # R near 1 -> every vector points the same way (laminar).
    # R near 0 -> directions cancel out (turbulent).
    # Using raw vectors rather than unit vectors weights fast movement more,
    # which is what we want: a few drifting pixels shouldn't outvote a surge.
    resultant = np.array([dx[moving].sum(), dy[moving].sum()])
    total_speed = float(mag_moving.sum())
    coherence = float(np.linalg.norm(resultant) / total_speed) if total_speed > 0 else 1.0

    # Spatial spread of speed. In turbulence some regions are pinned while
    # others are shoved — that shows up here as a high coefficient of variation.
    speed_dispersion = float(mag_moving.std() / (mag_moving.mean() + 1e-6))

    return {
        "mean_magnitude": float(mag_moving.mean()),
        "coherence": coherence,
        "speed_dispersion": speed_dispersion,
        "occupancy": occupancy,
    }


def _classify(mean_mag, coherence, dispersion, pulse_cv, occupancy):
    """Map metrics onto Helbing's phases."""
    # Not enough of the frame is moving for this to be crowd motion at all —
    # catches empty scenes and sensor noise before their random directions
    # can be mistaken for turbulence.
    if mean_mag < MOVING_MIN_MAG or occupancy < MIN_OCCUPANCY:
        return "STATIC"
    if coherence < COHERENCE_TURBULENT:
        return "TURBULENT"
    if pulse_cv > PULSE_CV_THRESHOLD:
        return "STOP_AND_GO"
    if coherence >= COHERENCE_LAMINAR:
        return "LAMINAR"
    # Coherence sits between the two thresholds: disordered, but not clearly
    # turbulent. Treated as the early edge of stop-and-go rather than calm,
    # because under-calling is the more dangerous error here.
    return "STOP_AND_GO"


def analyze_flow(clip_path, compensate_camera_motion=True):
    """Analyse one video chunk's motion field.

    Returns a dict of metrics plus a phase label. No network calls.
    """
    frames = _iter_gray_frames(clip_path)
    prev = next(frames, None)
    if prev is None:
        raise ValueError(f"No frames decoded from {clip_path}")

    per_pair = []
    for frame in frames:
        per_pair.append(_pair_metrics(prev, frame, compensate_camera_motion))
        prev = frame

    if not per_pair:
        raise ValueError(f"Need at least 2 frames to compute flow: {clip_path}")

    magnitudes = np.array([m["mean_magnitude"] for m in per_pair])
    coherences = np.array([m["coherence"] for m in per_pair])
    dispersions = np.array([m["speed_dispersion"] for m in per_pair])
    occupancies = np.array([m["occupancy"] for m in per_pair])

    # Stop-and-go waves are an oscillation in speed over time, so we look at
    # how much the mean speed swings across the chunk, not its average value.
    pulse_cv = float(magnitudes.std() / (magnitudes.mean() + 1e-6))

    mean_mag = float(magnitudes.mean())
    coherence = float(coherences.mean())
    dispersion = float(dispersions.mean())
    occupancy = float(occupancies.mean())

    # Helbing's warning metric is "crowd pressure" = local density x velocity
    # variance. We have no true density (that would need person detection,
    # which we deliberately don't do), so motion occupancy stands in for it.
    # This is a PROXY and an uncalibrated one — it is not persons/m^2, and it
    # should be described that way. It is useful as a relative trend on a
    # fixed camera, not as an absolute number.
    pressure_proxy = occupancy * dispersion * mean_mag

    phase = _classify(mean_mag, coherence, dispersion, pulse_cv, occupancy)

    return {
        "phase": phase,
        "mean_magnitude": mean_mag,
        "coherence": coherence,
        "speed_dispersion": dispersion,
        "occupancy": occupancy,
        "pulse_cv": pulse_cv,
        "pressure_proxy": pressure_proxy,
        "frame_pairs": len(per_pair),
        "timestamp": time.time(),
    }


def should_escalate(metrics):
    
    return metrics["phase"] in ("TURBULENT", "STOP_AND_GO")


def flow_events(metrics):

    phase = metrics["phase"]

    # Confidence is derived from how far from the ordered/coherent end the
    # motion sits. Deliberately not dressed up as a probability — it hasn't
    # been calibrated against labelled footage yet.
    disorder = float(np.clip(1.0 - metrics["coherence"], 0.0, 1.0))

    return [
        {
            "question": "crowd flow is turbulent",
            "match": phase == "TURBULENT",
            "confidence": disorder if phase == "TURBULENT" else 1.0 - disorder,
            "timestamp": metrics["timestamp"],
        },
        {
            "question": "crowd movement is pulsing in stop-and-go waves",
            "match": phase == "STOP_AND_GO",
            "confidence": float(np.clip(metrics["pulse_cv"], 0.0, 1.0)),
            "timestamp": metrics["timestamp"],
        },
    ]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m reel_it_in.vision.flow <clip_path> [--mounted]")
        raise SystemExit(1)

    compensate = "--mounted" not in sys.argv
    result = analyze_flow(sys.argv[1], compensate_camera_motion=compensate)

    print(f"\n  phase             {result['phase']}")
    print(f"  coherence         {result['coherence']:.3f}   (1 = one direction, 0 = chaotic)")
    print(f"  mean magnitude    {result['mean_magnitude']:.3f} px/frame")
    print(f"  speed dispersion  {result['speed_dispersion']:.3f}")
    print(f"  occupancy         {result['occupancy']:.3f}   (fraction of frame moving)")
    print(f"  pulse (temporal)  {result['pulse_cv']:.3f}   (stop-and-go signature)")
    print(f"  pressure proxy    {result['pressure_proxy']:.3f}   (uncalibrated)")
    print(f"  frame pairs       {result['frame_pairs']}")
    print(f"\n  escalate to Reka? {should_escalate(result)}\n")