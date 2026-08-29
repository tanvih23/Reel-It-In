"""
reel_it_in.highlights

This package turns raw Reka Vision results into a finished
highlight reel:

    1. selection.py -> pick the best, non-overlapping moments
    2. stitch.py     -> cut and glue those moments into one video

__main__.py wires this together with reel_it_in.vision.highlights
(the module that talks to the Reka API) so the whole thing can be
run as: python -m reel_it_in.highlights <video_path>
"""

from .selection import select_highlights, overlaps
from .stitch import create_highlight_reel

__all__ = [
    "select_highlights",
    "overlaps",
    "create_highlight_reel",
]