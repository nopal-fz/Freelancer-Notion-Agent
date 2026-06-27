import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

from app.config import settings
from app.telegram.sender import send_telegram_message
from app.telegram.commands import handle_telegram_command

router = APIRouter(prefix="/telegram", tags=["Telegram"])

logger = logging.getLogger(__name__)

# function to check if a user is allowed based on the allowed user IDs in settings
def is_user_allowed(user_id: int) -> bool:
    allowed_ids = settings.allowed_telegram_user_ids

    # Kalau kosong, artinya testing mode: semua user boleh.
    if not allowed_ids:
        return True

    return user_id in allowed_ids

def extract_message(update: dict[str, Any]) -> dict[str, Any] | None:
    return update.get("message") or update.get("edited_message")

# Webhook endpoint to handle incoming Telegram updates
@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
):
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(status_code=403, detail="Invalid Telegram secret token.")

    update = await request.json()
    message = extract_message(update)

    if not message:
        return {"ok": True, "message": "No message to process."}

    chat = message.get("chat", {})
    sender = message.get("from", {})

    chat_id = chat.get("id")
    user_id = sender.get("id")
    text = message.get("text")

    logger.info(
        "Incoming Telegram message | user_id=%s | chat_id=%s | text=%s",
        user_id,
        chat_id,
        text,
    )

    if not chat_id or not user_id:
        return {"ok": True, "message": "Missing chat_id or user_id."}

    if not is_user_allowed(user_id):
        await send_telegram_message(
            chat_id=chat_id,
            text="Maaf, kamu belum terdaftar sebagai pengguna FreelancerOS.",
        )
        return {"ok": True, "message": "Unauthorized user."}

    if not text:
        await send_telegram_message(
            chat_id=chat_id,
            text="Saat ini FreelancerOS baru bisa menerima pesan teks.",
        )
        return {"ok": True}

    try:
        reply_text = await handle_telegram_command(text)
    except Exception:
        logger.exception("Failed to process Telegram command.")
        reply_text = (
            "Maaf, terjadi error saat memproses command.\n"
            "Cek terminal FastAPI untuk detail error."
        )

    await send_telegram_message(chat_id=chat_id, text=reply_text)

    return {"ok": True}