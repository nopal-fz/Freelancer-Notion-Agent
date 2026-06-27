import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not telegram_bot_token:
        print("TELEGRAM_BOT_TOKEN is not configured.")
        raise SystemExit(1)

    telegram_api_url = (
        f"https://api.telegram.org/bot{telegram_bot_token}/setMyCommands"
    )

    payload = {
        "commands": [
            {
                "command": "help",
                "description": "Panduan command FreelancerOS",
            },
            {
                "command": "tasks",
                "description": "Lihat semua task",
            },
            {
                "command": "tasks_progress",
                "description": "Task In progress",
            },
            {
                "command": "tasks_done",
                "description": "Task Done",
            },
            {
                "command": "tasks_review",
                "description": "Task Under review",
            },
            {
                "command": "tasks_todo",
                "description": "Task Not started",
            },
            {
                "command": "add",
                "description": "Tambah task baru",
            },
            {
                "command": "receivables",
                "description": "Hitung piutang aktif",
            },
            {
                "command": "stats",
                "description": "Statistik task",
            },
            {
                "command": "report",
                "description": "Weekly freelancer report",
            },
            {
                "command": "receivables",
                "description": "Piutang aktif",
            },
            {
                "command": "receivables_progress",
                "description": "Piutang In progress",
            },
            {
                "command": "receivables_review",
                "description": "Piutang Under review",
            },
            {
                "command": "receivables_active",
                "description": "Piutang In progress + Under review",
            },
            {
                "command": "focus",
                "description": "Rekomendasi fokus hari ini",
            },
        ]
    }

    response = httpx.post(
        telegram_api_url,
        json=payload,
        timeout=10,
    )

    print("Status Code:", response.status_code)
    print("Response:", response.json())


if __name__ == "__main__":
    main()