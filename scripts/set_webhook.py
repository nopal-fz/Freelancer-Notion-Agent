import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

# Script to set the Telegram webhook URL for the bot
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/set_webhook.py https://your-public-url")
        raise SystemExit(1)

    public_url = sys.argv[1].rstrip("/")

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

    if not telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not configured.")
        raise SystemExit(1)

    webhook_url = f"{public_url}/telegram/webhook"
    telegram_api_url = f"https://api.telegram.org/bot{telegram_bot_token}/setWebhook"

    payload = {
        "url": webhook_url,
        "drop_pending_updates": True,
        "allowed_updates": ["message"],
    }

    if telegram_webhook_secret:
        payload["secret_token"] = telegram_webhook_secret

    response = httpx.post(telegram_api_url, json=payload, timeout=10)

    print("Webhook URL:", webhook_url)
    print("Status Code:", response.status_code)
    print("Response:", response.json())


if __name__ == "__main__":
    main()