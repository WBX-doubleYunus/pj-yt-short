"""Telegram helpers to notify and send generated shorts.

Functions:
- send_short_notification(short_path, transcript_path, highlights)
- send_text(message)

Requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in config (or pass chat_id explicitly).
"""
import os
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

try:
    from telegram import Bot
except Exception:
    Bot = None


def _ensure_bot():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not configured")
    if Bot is None:
        raise RuntimeError("python-telegram-bot not available; install requirements")
    return Bot(token=TELEGRAM_BOT_TOKEN)


def _generate_caption(transcript_path: str, highlights: list) -> str:
    lines = []
    lines.append("Hasil Short otomatis")
    if highlights:
        lines.append("Highlights:")
        for h in highlights:
            start = h.get("start")
            cap = h.get("caption") or ""
            lines.append(f"- {start:.1f}s: {cap}")
    if transcript_path and os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            text = f.read(500)
            if text:
                lines.append("\nTranskrip (potongan):")
                lines.append(text.replace('\n', ' ') + ("..." if len(text)>500 else ""))
    return "\n".join(lines)


def send_text(message: str, chat_id: str = None):
    bot = _ensure_bot()
    cid = chat_id or TELEGRAM_CHAT_ID
    if not cid:
        raise RuntimeError("TELEGRAM_CHAT_ID not configured")
    bot.send_message(chat_id=cid, text=message)


def _generate_thumbnail(video_path: str, thumb_path: str):
    import subprocess
    cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", "00:00:01", "-vframes", "1", thumb_path]
    subprocess.run(cmd, check=False)
    return thumb_path


def send_short_notification(short_path: str, transcript_path: str = None, highlights: list = None, chat_id: str = None):
    bot = _ensure_bot()
    cid = chat_id or TELEGRAM_CHAT_ID
    if not cid:
        raise RuntimeError("TELEGRAM_CHAT_ID not configured")

    caption = _generate_caption(transcript_path, highlights or [])

    # try to generate thumbnail
    thumb = None
    try:
        thumb = os.path.splitext(short_path)[0] + ".thumb.jpg"
        _generate_thumbnail(short_path, thumb)
    except Exception:
        thumb = None

    with open(short_path, "rb") as vid:
        # send video
        bot.send_video(chat_id=cid, video=vid, caption=caption, supports_streaming=True)

    # send thumbnail as separate message for preview if available
    if thumb and os.path.exists(thumb):
        with open(thumb, "rb") as ph:
            bot.send_photo(chat_id=cid, photo=ph, caption="Preview gambar highlight")

    # Send full transcript as a file if not too large
    if transcript_path and os.path.exists(transcript_path):
        size = os.path.getsize(transcript_path)
        if size < 5000000:  # <5MB
            with open(transcript_path, "rb") as tf:
                bot.send_document(chat_id=cid, document=tf, filename=os.path.basename(transcript_path))
        else:
            bot.send_message(chat_id=cid, text="Transkrip terlalu besar untuk diunggah; simpan lokal pada server.")
