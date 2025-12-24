"""Soundboard overlay utilities.

Strategy (prototype):
- Look into `assets/soundboard/` for sound files (mp3/wav).
- Map keyword -> file by file basename (e.g. `ding.mp3` -> keyword `ding`).
- Detect occurrences of keywords in transcription segments and schedule events (start time).
- Overlay events on top of original audio by invoking ffmpeg with adelay + amix.

Limitations: This is a simple prototype — overlapping effects are supported, but mixing/volume fine-tuning
and audio normalization are left for future improvement.
"""
import os
import glob
import subprocess
from typing import List, Dict

SOUND_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "soundboard")


def discover_sounds() -> Dict[str, str]:
    """Return mapping keyword -> filepath (keyword is basename without extension).
    Files are matched by name: e.g. `ding.mp3` maps to keyword `ding`.
    """
    mapping = {}
    if not os.path.isdir(SOUND_DIR):
        return mapping
    for p in glob.glob(os.path.join(SOUND_DIR, "*.*")):
        name = os.path.splitext(os.path.basename(p))[0].lower()
        mapping[name] = p
    return mapping


def detect_sound_events(segments: List[dict]) -> List[dict]:
    """Detect sound events from segments.

    Returns list of events: {start: float, sound_file: str}
    """
    mapping = discover_sounds()
    events = []
    for seg in segments:
        txt = seg.get("text", "").lower()
        start = seg.get("start", 0.0)
        # simple matching: if keyword appears in segment, schedule at segment start
        for kw, path in mapping.items():
            if kw in txt:
                events.append({"start": start, "sound_file": path})
    return events


def overlay_soundboard(video_in: str, events: List[dict], out_path: str) -> str:
    """Overlay detected events onto the video's audio and write out_path video with mixed audio.

    Approach: use ffmpeg with multiple -i inputs (video + one per event), apply adelay for each
    sound input, and amix them with original audio.

    This function will skip if there are no events or no sound files available.
    """
    if not events:
        # just copy
        subprocess.run(["ffmpeg", "-y", "-i", video_in, "-c", "copy", out_path], check=False)
        return out_path

    # Build command with inputs
    cmd = ["ffmpeg", "-y", "-i", video_in]
    sound_inputs = []
    for e in events:
        sf = e.get("sound_file")
        if os.path.exists(sf):
            cmd += ["-i", sf]
            sound_inputs.append(e)
    if not sound_inputs:
        subprocess.run(["ffmpeg", "-y", "-i", video_in, "-c", "copy", out_path], check=False)
        return out_path

    # Build filter_complex
    filter_parts = []
    s_labels = []
    for i, e in enumerate(sound_inputs):
        idx = i + 1  # because 0 is the main video
        delay_ms = int(e.get("start", 0.0) * 1000)
        # adelay expects something like '1000|1000' for stereo, but most effects are mono; use single value
        filter_parts.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[s{idx}]")
        s_labels.append(f"[s{idx}]")

    # amix all: original audio [0:a] + all s_labels
    all_inputs = "".join(s_labels)
    inputs_count = 1 + len(s_labels)
    amix = f"[0:a]{all_inputs}amix=inputs={inputs_count}:dropout_transition=0[aout]"

    filter_complex = ";".join(filter_parts + [amix])
    full_cmd = cmd + ["-filter_complex", filter_complex, "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", out_path]
    subprocess.run(full_cmd, check=False)
    return out_path
