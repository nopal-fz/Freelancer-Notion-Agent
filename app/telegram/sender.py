import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# This function sends a message to a specified Telegram chat using the Telegram Bot API
async def send_telegram_message(chat_id: int, text: str) -> dict:
    url = f"{settings.telegram_api_base_url}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, json=payload)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        logger.exception("Failed to send Telegram message.")
        raise

    return response.json()