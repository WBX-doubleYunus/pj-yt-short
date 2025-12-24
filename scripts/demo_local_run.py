"""Demo script: create a dummy input, patch environment for a no-op run, and execute pipeline.

Usage: python scripts/demo_local_run.py
This is intended for local dev and uses subprocess.run stubs via environment variable
`YT_SHORT_DEMO_NO_OP` to avoid running external commands if set to '1'.
"""
import os
import shutil
import subprocess
from app import process

OUT = os.path.join(os.path.dirname(__file__), "..", "outputs", "tmp")
if not os.path.exists(OUT):
    os.makedirs(OUT, exist_ok=True)

# create dummy input
infile = os.path.join(OUT, "input.mp4")
with open(infile, "wb") as f:
    f.write(b"dummy-video-data")

# If requested, make subprocess.run a no-op by setting env var
if os.getenv("YT_SHORT_DEMO_NO_OP") == "1":
    import subprocess as _sub
    _sub.run = lambda *a, **k: None

print("Running demo pipeline...")
res = process.handle_new_video("https://example.com/watch?v=demo", max_duration=10)
print("Result:", res)
print("Processed marker:", os.path.exists(os.path.join(OUT, "processed.txt")))
