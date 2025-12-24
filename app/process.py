"""High-level processing pipeline (dev).

Current scaffold implements download and a simple trim-to-length step. Later steps
will fill in transcription, moderation, highlight extraction, subtitles, and soundboard.
"""
import subprocess
import os
import glob
from .config import OUTPUT_DIR, SHORT_MAX_SECONDS


def _latest_downloaded_file(tmp_dir: str):
    files = glob.glob(os.path.join(tmp_dir, "input.*"))
    if not files:
        return None
    # pick the first match
    return files[0]


def handle_new_video(youtube_url: str, max_duration: int = SHORT_MAX_SECONDS):
    # 1) Download video (yt-dlp)
    out_dir = os.path.join(OUTPUT_DIR, "tmp")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "input.%(ext)s")
    cmd = ["yt-dlp", "-f", "best", "-o", out_path, youtube_url]
    subprocess.run(cmd, check=False)

    in_file = _latest_downloaded_file(out_dir)
    if not in_file:
        raise RuntimeError("download failed or no file found")

    # 2) Create a short by trimming to max_duration seconds (simple heuristic: start at 0)
    short_path = os.path.join(out_dir, "short.mp4")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        in_file,
        "-ss",
        "0",
        "-t",
        str(max_duration),
        "-vf",
        "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:-1:-1:black",
        "-c:a",
        "aac",
        "-c:v",
        "libx264",
        short_path,
    ]
    subprocess.run(ffmpeg_cmd, check=False)

    # 3) Transcribe audio using OpenAI Whisper (via HTTP helper)
    try:
        from .transcribe import transcribe_from_video

        # transcribe and get segments (if available). We expect transcribe_from_video to return raw text,
        # but we'll also try to get more structured segments if available from the JSON response.
        transcript_text = transcribe_from_video(in_file, language="id")
        transcript_path = os.path.join(out_dir, "transcript.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)

        # try to load segments if the transcribe helper saved them
        seg_path = os.path.join(out_dir, "audio.segments.json")
        # Default to a single full-range segment
        segments = [{"start": 0.0, "end": float(max_duration), "text": transcript_text}]
        # The transcribe helper saves segments next to the audio temp file with .segments.json suffix
        # Try to find any .segments.json in the temp dir
        import glob, json

        seg_files = glob.glob(os.path.join(out_dir, "*.segments.json"))
        if seg_files:
            try:
                with open(seg_files[0], "r", encoding="utf-8") as sf:
                    segments = json.load(sf)
            except Exception:
                pass
    except Exception as e:
        with open(os.path.join(out_dir, "transcribe_error.txt"), "w", encoding="utf-8") as f:
            f.write(str(e))
        transcript_text = ""
        segments = []

    # 4) Moderation (SARA) detection & censoring (bleep + redact + blur)
    try:
        from .moderation import moderate_segments
        from .censor import segments_to_srt, bleep_audio_for_segments, blur_video_segments, replace_audio_in_video

        flagged_idxs = moderate_segments(segments)
        flagged_segments = [segments[i] for i in flagged_idxs]

        # Create subtitles (SRT) with redaction
        srt_path = os.path.join(out_dir, "subtitles.srt")
        segments_to_srt(segments, flagged_idxs, srt_path)

        if flagged_idxs:
            # 4a) Bleep audio for flagged segments
            bleeped_audio = os.path.join(out_dir, "audio_bleep.mp3")
            bleep_audio_for_segments(short_path, segments, flagged_idxs, bleeped_audio)
            # 4b) Replace audio in video
            bleeped_video = os.path.join(out_dir, "short_bleeped.mp4")
            replace_audio_in_video(short_path, bleeped_audio, bleeped_video)
            # 4c) Blur video during flagged segments
            censored_video = os.path.join(out_dir, "short_censored.mp4")
            blur_video_segments(bleeped_video, flagged_segments, censored_video)
            final_video = censored_video
        else:
            final_video = short_path
    except Exception as e:
        # on errors continue with the trimmed short
        with open(os.path.join(out_dir, "censor_error.txt"), "w", encoding="utf-8") as f:
            f.write(str(e))
        final_video = short_path

    # 5) Burn-in subtitles
    try:
        from .subtitles import burn_subtitles_into_video
        from .soundboard import detect_sound_events, overlay_soundboard
        from .highlight import extract_highlights
        from .visual_overlay import overlay_images_on_video

        subtitled = os.path.join(out_dir, "short_subtitled.mp4")
        burn_subtitles_into_video(final_video, srt_path, subtitled)

        # 5a) extract highlights (labels like 'funny' will be used to overlay sound/images)
        highlights = extract_highlights(transcript_text)

        # 5b) Convert highlights into sound events and image overlay events
        sound_events = detect_sound_events(segments)  # existing keyword-based detection
        # also add events from highlight labels
        img_events = []
        for h in highlights:
            lbl = h.get("label", "").lower()
            start = h.get("start", 0.0)
            end = h.get("end", start + 2.0)
            # if label is funny, try to add default sound 'funny' if available
            if lbl == "funny":
                # schedule sound at highlight start; soundboard overlay will map keyword 'funny' to a file
                sound_events.append({"start": start, "sound_file": None, "label": "funny"})
                # schedule image overlay: look for assets/images/funny.*
                img_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "images")
                import glob

                img_files = glob.glob(os.path.join(img_dir, "funny.*"))
                if img_files:
                    img_events.append({"start": start, "end": end, "image": img_files[0]})
        # merge and apply sounds
        # map sound_events entries with label to actual files via soundboard discover
        from .soundboard import discover_sounds

        mapping = discover_sounds()
        concrete_events = []
        for e in sound_events:
            if e.get("sound_file"):
                concrete_events.append(e)
            else:
                lbl = e.get("label")
                if lbl and lbl in mapping:
                    concrete_events.append({"start": e.get("start"), "sound_file": mapping[lbl]})

        if concrete_events:
            with_sounds = os.path.join(out_dir, "short_with_sounds.mp4")
            overlay_soundboard(subtitled, concrete_events, with_sounds)
        else:
            with_sounds = subtitled

        # apply image overlays if any
        if img_events:
            with_images = os.path.join(out_dir, "short_with_images.mp4")
            overlay_images_on_video(with_sounds, img_events, with_images)
            final_with_sounds = with_images
        else:
            final_with_sounds = with_sounds

    except Exception as e:
        with open(os.path.join(out_dir, "subtitle_sound_error.txt"), "w", encoding="utf-8") as f:
            f.write(str(e))
        final_with_sounds = final_video

    # 6) create a marker file for dev
    open(os.path.join(out_dir, "processed.txt"), "w").write("done")

    # 7) Send notification via Telegram (if configured)
    try:
        from .telegram import send_short_notification
        send_short_notification(final_with_sounds, transcript_path if transcript_text else None, highlights)
    except Exception as e:
        # write a non-fatal notification error for inspection
        with open(os.path.join(out_dir, "telegram_error.txt"), "w", encoding="utf-8") as f:
            f.write(str(e))

    return {"short": final_with_sounds, "transcript_file": transcript_path if transcript_text else None, "subtitles": srt_path, "highlights": highlights}
