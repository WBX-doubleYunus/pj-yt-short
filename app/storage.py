import json
import os
from .config import OUTPUT_DIR

STATE_FILE = os.path.join(OUTPUT_DIR, "state.json")


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_last_video_for_channel(channel_id: str):
    state = _load_state()
    return state.get(channel_id)


def set_last_video_for_channel(channel_id: str, video_id: str):
    state = _load_state()
    state[channel_id] = video_id
    _save_state(state)
