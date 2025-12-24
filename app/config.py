import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
OAUTH_REDIRECT = os.getenv("OAUTH_REDIRECT", "http://localhost:8000/auth/callback")
SHORT_MAX_SECONDS = int(os.getenv("SHORT_MAX_SECONDS", "120"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
