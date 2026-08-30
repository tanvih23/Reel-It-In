"""Generate synthetic crowd-like clips with known motion character,
to check flow.py's metrics actually discriminate."""
import numpy as np
import cv2

W, H, N_DOTS, FPS, SECONDS = 640, 360, 400, 15, 4
rng = np.random.default_rng(42)


def render(positions):
    frame = np.full((H, W, 3), 30, np.uint8)
    for x, y in positions:
        cv2.circle(frame, (int(x) % W, int(y) % H), 5, (200, 200, 200), -1)
    return frame


def write(path, step_fn):
    pos = np.column_stack([rng.uniform(0, W, N_DOTS), rng.uniform(0, H, N_DOTS)])
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for t in range(FPS * SECONDS):
        out.write(render(pos))
        pos = step_fn(pos, t)
    out.release()
    print("wrote", path)


# LAMINAR: everyone drifts the same direction, small jitter
write("/home/claude/test_laminar.mp4",
      lambda p, t: p + np.array([2.0, 0.0]) + rng.normal(0, 0.15, p.shape))

# TURBULENT: each dot shoved in its own random direction, re-randomised often
def turbulent(p, t):
    return p + rng.normal(0, 2.5, p.shape)
write("/home/claude/test_turbulent.mp4", turbulent)

# STOP_AND_GO: coherent direction, but speed pulses between fast and frozen
def stopgo(p, t):
    speed = 3.0 if (t // 7) % 2 == 0 else 0.05
    return p + np.array([speed, 0.0]) + rng.normal(0, 0.15, p.shape)
write("/home/claude/test_stopgo.mp4", stopgo)

# STATIC: essentially nothing happening
write("/home/claude/test_static.mp4",
      lambda p, t: p + rng.normal(0, 0.05, p.shape))