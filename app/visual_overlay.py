"""Visual overlay helpers: overlay images (PNG) at specific times on a video.

Prototype approach: apply overlays sequentially (one event per ffmpeg call) for simplicity.
Events format: [{"start": float, "end": float, "image": "/path/to/img.png"}, ...]
"""
import os
import subprocess
from typing import List


def overlay_images_on_video(video_in: str, events: List[dict], out_path: str) -> str:
    tmp = video_in
    idx = 0
    for ev in events:
        img = ev.get("image")
        if not img or not os.path.exists(img):
            continue
        start = float(ev.get("start", 0.0))
        end = float(ev.get("end", start + 2.0))
        duration = end - start
        # build an ffmpeg command to overlay image with enable between(t,start,end)
        out_tmp = f"{os.path.splitext(out_path)[0]}.ov{idx}.mp4"
        vf = f"overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2:enable='between(t,{start},{end})'"
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            tmp,
            "-i",
            img,
            "-filter_complex",
            vf,
            "-c:a",
            "copy",
            out_tmp,
        ]
        subprocess.run(cmd, check=False)
        tmp = out_tmp
        idx += 1
    # final copy to out_path
    if tmp != out_path:
        subprocess.run(["ffmpeg", "-y", "-i", tmp, "-c", "copy", out_path], check=False)
    return out_path
