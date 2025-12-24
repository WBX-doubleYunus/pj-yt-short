"""Transcription helpers using OpenAI Whisper endpoint (HTTP).

This module extracts audio from a video file and sends it to OpenAI's
/audio/transcriptions endpoint using httpx to avoid depending on a specific
openai SDK method name.
"""
import os
import subprocess
import tempfile
import httpx
from .config import OPENAI_API_KEY

OPENAI_TRANSCRIPT_URL = "https://api.openai.com/v1/audio/transcriptions"


def _extract_audio(video_path: str, out_path: str):
    # extract audio to a single channel mp3 for Whisper
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "libmp3lame",
        "-ac",
        "1",
        "-ar",
        "16000",
        out_path,
    ]
    subprocess.run(cmd, check=False)
    return out_path


def transcribe_audio_file(audio_path: str, language: str = "id") -> str:
    """Send an audio file to OpenAI Whisper and return the transcription text.

    Attempts to request `verbose_json` for segment timestamps; if not available, falls back
    to plain text.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not configured")

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    # Model set to whisper-1
    data = {"model": "whisper-1", "language": language, "response_format": "verbose_json"}

    with open(audio_path, "rb") as fh:
        files = {"file": (os.path.basename(audio_path), fh, "audio/mpeg")}
        with httpx.Client(timeout=120) as client:
            r = client.post(OPENAI_TRANSCRIPT_URL, headers=headers, data=data, files=files)
            r.raise_for_status()
            j = r.json()
            # If verbose_json is returned it has `segments` and `text`.
            if isinstance(j, dict) and j.get("segments"):
                # Build a readable text and also save segments as a side effect
                text = j.get("text", "")
                segments = []
                for s in j.get("segments", []):
                    segments.append({"start": s.get("start", 0.0), "end": s.get("end", s.get("start", 0.0) + 1.0), "text": s.get("text", "").strip()})
                # Save segments as a JSON side-file for later use
                try:
                    import json
                    seg_path = os.path.splitext(audio_path)[0] + ".segments.json"
                    with open(seg_path, "w", encoding="utf-8") as sf:
                        json.dump(segments, sf, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                return text
            # fallback
            return j.get("text", "")


def transcribe_from_video(video_path: str, language: str = "id") -> str:
    """Extract audio from `video_path`, transcribe it, and return the text."""
    with tempfile.TemporaryDirectory() as td:
        audio_path = os.path.join(td, "audio.mp3")
        _extract_audio(video_path, audio_path)
        text = transcribe_audio_file(audio_path, language=language)
        return text
