# Dev helper: endpoint to test Telegram integration
from fastapi import APIRouter, BackgroundTasks
from .telegram import send_text

router = APIRouter()


@router.post("/telegram/test")
async def telegram_test(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_text, "Tes notifikasi dari yt-short-proto (bot)")
    return {"status": "queued"}
