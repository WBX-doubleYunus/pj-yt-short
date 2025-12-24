from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from . import oauth, youtube_monitor, process
from .config import SHORT_MAX_SECONDS
from .telegram_test_endpoint import router as telegram_test_router

app.include_router(telegram_test_router)

app = FastAPI(title="yt-short-proto")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/auth/start")
async def auth_start():
    url = oauth.get_authorize_url()
    return RedirectResponse(url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "missing code"}, status_code=400)
    oauth.finish_flow(code)
    return JSONResponse({"status": "authorized"})


@app.post("/monitor/run_once")
async def monitor_run_once(background_tasks: BackgroundTasks):
    # Run a single check for new uploads (dev)
    if not oauth.TOKENS.get("access_token"):
        return JSONResponse({"error": "not authorized"}, status_code=400)
    background_tasks.add_task(youtube_monitor.check_subscriptions_once)
    return {"status": "monitor_queued"}


@app.post("/simulate_video")
async def simulate_video(background_tasks: BackgroundTasks):
    # Dev helper: simulate a new upload to trigger processing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    background_tasks.add_task(process.handle_new_video, test_url, max_duration=SHORT_MAX_SECONDS)
    return {"status": "queued", "url": test_url}
