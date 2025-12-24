# YouTube-to-Shorts Prototype

Prototype pipeline to monitor subscribed YouTube channels, detect new uploads, transcribe and extract highlights, censor SARA content, generate a 9:16 short with Indonesian subtitles and soundboard overlays, and notify via Telegram.

## Quickstart

1. Copy `.env.example` to `.env` and fill keys: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`.
2. Register OAuth redirect `http://localhost:8000/auth/callback` in Google Cloud Console.
3. Install deps: `pip install -r requirements.txt`.
4. Start dev server: `uvicorn app.main:app --reload`.
5. Open `http://localhost:8000/auth/start` to authorize YouTube OAuth.
6. Use `/simulate_video` to trigger a test processing pipeline (for dev).

Development helpers:
- `POST /monitor/run_once` — run a single subscription check and trigger processing for any new uploads (requires OAuth).

Outputs will be written to `./outputs` by default.

---

Testing & demo

- Unit tests: run `pytest tests/` (install pytest). Tests mock external calls so they don't require keys.
- Demo runner: `python scripts/demo_local_run.py` (set `YT_SHORT_DEMO_NO_OP=1` to avoid running ffmpeg/yt-dlp).

Continuous Integration (GitHub Actions)

- I added a CI workflow `.github/workflows/ci.yml` that runs on push and pull requests: it installs system deps (ffmpeg), installs Python deps, runs `pytest`, and runs `scripts/demo_local_run.py` with `YT_SHORT_DEMO_NO_OP=1`.
- To run tests remotely (no local setup required): push the repository to GitHub (use `scripts/push-to-github.sh`), and the workflow will run automatically.

Docker

- A `Dockerfile` and `docker-compose.yml` are included to run the app in a container (ffmpeg included). Example:

  docker build -t yt-short-proto .
  docker run --rm -p 8000:8000 --env-file .env yt-short-proto

Local bootstrap (Windows)

- `scripts/bootstrap.ps1` helps install Python (via `winget` if available), create a venv, and install dependencies. Run it in PowerShell.

See `app/` for implementation and `scripts/` for helper scripts.
