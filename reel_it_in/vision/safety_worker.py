"""Entrypoint for `python -m reel_it_in.vision.safety_worker`. Owner: Tanvi."""

# TODO: watch CHUNK_DIR, run safety.analyze on each new chunk,
# TODO: pass results through middleware, write survivors to the events DB,
# TODO: purge the chunk once analyzed (no footage retained)
