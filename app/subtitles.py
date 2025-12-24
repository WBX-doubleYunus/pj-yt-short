"""Subtitle burn-in helpers using ffmpeg.
"""
import subprocess
import os


def burn_subtitles_into_video(video_in: str, srt_path: str, out_path: str, font_size: int = 36):
    # Use ffmpeg subtitles filter to burn SRT into the video
    # Note: srt_path may need to be absolute to avoid ffmpeg parsing issues
    srt_abs = os.path.abspath(srt_path)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_in,
        "-vf",
        f"subtitles={srt_abs}:force_style='FontName=Arial,FontSize={font_size},PrimaryColour=&HFFFFFF&'",
        "-c:a",
        "copy",
        out_path,
    ]
    subprocess.run(cmd, check=False)
    return out_path
