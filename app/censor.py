"""Censoring helpers: create redacted subtitles, bleep audio for flagged segments, and blur video during segments.

Uses pydub to manipulate audio and ffmpeg for video blur and subtitle burn-in.
"""
import os
import tempfile
import subprocess
from pydub import AudioSegment, generators


def segments_to_srt(segments, flagged_indexes, out_path):
    """Write an SRT file where flagged segments are redacted."""
    def fmt_time(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        ms = int((s - int(s)) * 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    lines = []
    for idx, seg in enumerate(segments, start=1):
        start = seg.get("start", 0.0)
        end = seg.get("end", start + 1.0)
        text = seg.get("text", "")
        if (idx - 1) in flagged_indexes:
            text = "[REDACTED]"
        lines.append(f"{idx}")
        lines.append(f"{fmt_time(start)} --> {fmt_time(end)}")
        lines.append(text)
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


def bleep_audio_for_segments(video_path, segments, flagged_indexes, out_audio_path):
    """Extract audio, replace flagged segments with a beep, and write result to out_audio_path.

    Returns path to modified audio file.
    """
    tmpdir = tempfile.mkdtemp()
    audio_raw = os.path.join(tmpdir, "audio_raw.mp3")
    # extract audio
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-ac", "1", "-ar", "16000", audio_raw]
    subprocess.run(cmd, check=False)

    audio = AudioSegment.from_file(audio_raw)
    for idx in flagged_indexes:
        seg = segments[idx]
        start_ms = int(seg.get("start", 0) * 1000)
        end_ms = int(seg.get("end", start_ms / 1000.0) * 1000)
        if end_ms <= start_ms:
            end_ms = start_ms + 1000
        duration_ms = end_ms - start_ms
        # generate beep
        sine = generators.Sine(1000)
        beep = sine.to_audio_segment(duration=duration_ms).apply_gain(-6.0)
        # replace the slice with beep
        audio = audio[:start_ms] + beep + audio[end_ms:]

    audio.export(out_audio_path, format="mp3")
    return out_audio_path


def blur_video_segments(in_path, flagged_segments, out_path):
    """Apply boxblur to the *entire frame* during flagged segments (simple prototype).

    `flagged_segments` is list of dicts with start/end in seconds.
    """
    if not flagged_segments:
        # nothing to do; copy
        subprocess.run(["ffmpeg", "-y", "-i", in_path, "-c", "copy", out_path], check=False)
        return out_path

    # Build enable expression
    expr_parts = []
    for s in flagged_segments:
        start = float(s.get("start", 0))
        end = float(s.get("end", start + 1.0))
        expr_parts.append(f"between(t,{start},{end})")
    expr = "+".join(expr_parts)
    # Apply boxblur only when expr is true
    vf = f"boxblur=10:1:cr=2:enable='{expr}'"
    cmd = ["ffmpeg", "-y", "-i", in_path, "-vf", vf, "-c:a", "copy", out_path]
    subprocess.run(cmd, check=False)
    return out_path


def replace_audio_in_video(video_in, audio_in, out_path):
    cmd = ["ffmpeg", "-y", "-i", video_in, "-i", audio_in, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", out_path]
    subprocess.run(cmd, check=False)
    return out_path
