"""Moderation helpers: uses OpenAI Moderation and a local keyword list for SARA detection.

Functions:
- moderate_text(text) -> bool/response: call OpenAI moderation endpoint
- moderate_segments(segments) -> list of flagged segment indexes
- load_local_keywords() -> list of keywords
"""
import os
import httpx
from typing import List
from .config import OPENAI_API_KEY

KEYWORDS_FILE = os.path.join(os.path.dirname(__file__), "..", "sara_keywords.txt")


def load_local_keywords() -> List[str]:
    if not os.path.exists(KEYWORDS_FILE):
        return []
    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        kws = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    return kws


MODERATION_URL = "https://api.openai.com/v1/moderations"


def moderate_text(text: str) -> dict:
    """Call OpenAI moderation endpoint and return the JSON response (or empty dict on error)."""
    if not OPENAI_API_KEY:
        return {}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"input": text}
    try:
        with httpx.Client(timeout=30) as client:
            r = client.post(MODERATION_URL, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()
    except Exception:
        return {}


def moderate_segments(segments: List[dict]) -> List[int]:
    """Given segments (each with 'start','end','text'), return list of indexes flagged as SARA.

    Strategy: run OpenAI moderation per segment if key present, and also check local keyword list.
    """
    kws = [k.lower() for k in load_local_keywords()]
    flagged = []
    for i, s in enumerate(segments):
        txt = s.get("text", "")
        lower = txt.lower()
        is_flagged = False
        # local keyword check
        for k in kws:
            if k and k in lower:
                is_flagged = True
                break
        # moderation API
        if not is_flagged and OPENAI_API_KEY:
            res = moderate_text(txt)
            # best-effort: check `results` or `model` response; OpenAI moderation returns `results` list
            try:
                results = res.get("results") or []
                if results:
                    r0 = results[0]
                    if r0.get("flagged"):
                        is_flagged = True
            except Exception:
                pass
        if is_flagged:
            flagged.append(i)
    return flagged
