"""Highlight extraction using OpenAI GPT to identify moments (e.g., funny moments) with timestamps.

The helper sends a prompt with the transcript and asks GPT to return a JSON array of highlights:
[{"start": 12.3, "end": 14.7, "label": "funny", "caption": "Punchline: ..."}, ...]

This is a best-effort heuristic for prototyping.
"""
import os
import httpx
import json
from .config import OPENAI_API_KEY

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def extract_highlights(transcript_text: str, max_highlights: int = 5) -> list:
    """Return a list of highlights with start/end/label/caption.

    If the API fails, returns an empty list.
    """
    if not OPENAI_API_KEY or not transcript_text:
        return []

    prompt = (
        "You are a tool that extracts short highlight moments from a video's transcript. "
        "Return a JSON array (no extra text) where each item has keys: start (seconds), end (seconds), "
        "label (one of: funny, important, sensitive, other) and caption (short Indonesian sentence). "
        "Provide up to {max_highlights} highlights, prioritize moments that would make a good short, and "
        "prefer shorter segments (1-10s). Use Indonesian for captions."
    ).replace("{max_highlights}", str(max_highlights))

    system = "You are a helpful assistant that outputs strict JSON." 
    user = f"Transcript:\n\n{transcript_text}\n\nExtract highlights as instructed."

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt + "\n\n" + user},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    try:
        with httpx.Client(timeout=60) as client:
            r = client.post(OPENAI_CHAT_URL, headers=headers, json=payload)
            r.raise_for_status()
            j = r.json()
            # get assistant content
            cont = j["choices"][0]["message"]["content"]
            # attempt to parse JSON from content
            # Some assistants may wrap json in ```; try to extract the first JSON array
            txt = cont.strip()
            # naive extraction
            start_idx = txt.find("[")
            end_idx = txt.rfind("]")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = txt[start_idx : end_idx + 1]
                try:
                    arr = json.loads(json_text)
                    # sanitize entries
                    out = []
                    for it in arr:
                        try:
                            start = float(it.get("start", 0.0))
                            end = float(it.get("end", start + 2.0))
                            label = it.get("label", "other")
                            caption = it.get("caption", "")
                            out.append({"start": start, "end": end, "label": label, "caption": caption})
                        except Exception:
                            continue
                    return out
                except Exception:
                    return []
            return []
    except Exception:
        return []
