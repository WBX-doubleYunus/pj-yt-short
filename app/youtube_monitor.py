"""YouTube monitoring helpers (dev).

This file contains a small polling / one-off checker that uses the OAuth credentials
stored in `oauth.TOKENS` to list subscriptions and detect new uploads. On new upload
it will call into the main processing pipeline.
"""
import requests
from .oauth import TOKENS
from . import process
from .storage import get_last_video_for_channel, set_last_video_for_channel

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def _auth_headers():
    token = TOKENS.get("access_token")
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def check_subscriptions_once():
    """One-off check: list the authenticated user's subscriptions and look for new uploads.
    This is meant for dev/testing; production should be event-driven or scheduled.
    """
    headers = _auth_headers()
    if not headers:
        # not authorized
        return {"error": "not_authorized"}

    # 1) Get subscriptions (paginated, simple dev version 50 max)
    subs_url = f"{YOUTUBE_API_BASE}/subscriptions?part=snippet&mine=true&maxResults=50"
    r = requests.get(subs_url, headers=headers)
    if r.status_code != 200:
        return {"error": "api_error", "details": r.text}

    subs = r.json().get("items", [])
    found = []
    for s in subs:
        channel_id = s["snippet"]["resourceId"]["channelId"]

        # 2) Fetch latest video for channel (search endpoint)
        search_url = f"{YOUTUBE_API_BASE}/search?part=snippet&channelId={channel_id}&order=date&type=video&maxResults=1"
        rs = requests.get(search_url, headers=headers)
        if rs.status_code != 200:
            continue
        items = rs.json().get("items", [])
        if not items:
            continue
        latest = items[0]
        video_id = latest["id"]["videoId"]
        last_seen = get_last_video_for_channel(channel_id)
        if last_seen != video_id:
            # new video found
            found.append({"channel_id": channel_id, "video_id": video_id})
            # mark immediately to avoid duplicate processing
            set_last_video_for_channel(channel_id, video_id)
            # trigger processing (simple, synchronous call may be replaced by background task)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            try:
                process.handle_new_video(video_url)
            except Exception as e:
                # in production use logging
                print("Error processing video:", e)

    return {"checked": len(subs), "new": len(found), "found": found}
