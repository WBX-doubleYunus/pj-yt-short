"""Minimal OAuth helpers (dev scaffold).

This uses google_auth_oauthlib to create an authorization URL and exchange code for tokens.
For production, persist refresh tokens securely.
"""
from google_auth_oauthlib.flow import Flow
from .config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, OAUTH_REDIRECT

# For demo we keep tokens in memory
TOKENS = {}

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]


def get_authorize_url():
    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [OAUTH_REDIRECT],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = OAUTH_REDIRECT
    auth_url, _ = flow.authorization_url(access_type="offline", include_granted_scopes="true")
    return auth_url


def finish_flow(code: str):
    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [OAUTH_REDIRECT],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = OAUTH_REDIRECT
    flow.fetch_token(code=code)
    creds = flow.credentials
    TOKENS["access_token"] = creds.token
    TOKENS["refresh_token"] = creds.refresh_token
    TOKENS["scopes"] = creds.scopes
    # In production, persist tokens to DB or secure store
    return TOKENS
