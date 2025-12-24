"""Dev helper to download a YouTube URL and run the pipeline (calls app.process functions).

Usage:
    python scripts/download_and_process.py <youtube_url>
"""
import sys
import subprocess
from app.process import handle_new_video


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/download_and_process.py <youtube_url>")
        return
    url = sys.argv[1]
    handle_new_video(url)


if __name__ == "__main__":
    main()
