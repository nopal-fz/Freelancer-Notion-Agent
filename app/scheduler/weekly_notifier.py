from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.memory.redis_memory import RedisMemory
from app.mcp_client.notion_mcp_client import NotionMCPClient
from app.telegram.sender import send_telegram_message
from app.telegram.commands import format_rupiah

logger = logging.getLogger(__name__)

def format_weekly_notification(
    weekly_data: dict,
    focus_data: dict,
) -> str:
    upcoming_deadlines = weekly_data.get("upcoming_deadlines") or []
    recommended_tasks = focus_data.get("tasks") or []

    lines = [
        "📊 Weekly FreelancerOS Report",
        "",
        f"✅ Completed: {weekly_data.get('tasks_completed', 0)}",
        f"🟡 Active: {weekly_data.get('tasks_active', 0)}",
        f"⚪ Not Started: {weekly_data.get('tasks_not_started', 0)}",
        f"🧪 Under Review: {weekly_data.get('tasks_under_review', 0)}",
        f"🔴 Overdue: {weekly_data.get('tasks_overdue', 0)}",
        "",
        f"🧾 Outstanding Payments: {format_rupiah(weekly_data.get('outstanding_payments'))}",
        "",
        "📅 Upcoming Deadlines:",
    ]

    if upcoming_deadlines:
        for index, task in enumerate(upcoming_deadlines[:5], start=1):
            lines.append(
                f"{index}. {task.get('task_name')} — {task.get('due_date')} "
                f"({task.get('priority')})"
            )
    else:
        lines.append("- Tidak ada deadline dalam 7 hari ke depan.")

    lines.append("")
    lines.append("🎯 Rekomendasi Fokus:")

    if recommended_tasks:
        for index, task in enumerate(recommended_tasks[:5], start=1):
            lines.append(
                f"{index}. {task.get('task_name')}\n"
                f"   Score: {task.get('priority_score')}\n"
                f"   Status: {task.get('status')}\n"
                f"   Deadline: {task.get('due_date') or '-'}"
            )
    else:
        lines.append("- Belum ada rekomendasi fokus.")

    return "\n".join(lines)


async def send_weekly_report_to_all_users() -> None:
    logger.info("Running weekly FreelancerOS notification job.")

    memory = RedisMemory()
    mcp_client = NotionMCPClient()

    try:
        chat_ids = await memory.get_chat_ids()

        if not chat_ids:
            logger.warning("No Telegram chat IDs found in Redis.")
            return

        weekly_result = await mcp_client.weekly_summary()
        focus_result = await mcp_client.recommend_today_focus(limit=5)

        if not weekly_result.get("success"):
            logger.error("weekly_summary failed: %s", weekly_result.get("message"))
            return

        if not focus_result.get("success"):
            logger.error("recommend_today_focus failed: %s", focus_result.get("message"))
            return

        weekly_data = weekly_result.get("data") or {}
        focus_data = focus_result.get("data") or {}

        message = format_weekly_notification(
            weekly_data=weekly_data,
            focus_data=focus_data,
        )

        for chat_id in chat_ids:
            await send_telegram_message(
                chat_id=chat_id,
                text=message,
            )

        logger.info("Weekly report sent to %s chat(s).", len(chat_ids))

    finally:
        await memory.close()


async def run_scheduler() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    scheduler = AsyncIOScheduler(
        timezone=settings.WEEKLY_REPORT_TIMEZONE,
    )

    scheduler.add_job(
        send_weekly_report_to_all_users,
        CronTrigger(
            day_of_week=settings.WEEKLY_REPORT_DAY_OF_WEEK,
            hour=settings.WEEKLY_REPORT_HOUR,
            minute=settings.WEEKLY_REPORT_MINUTE,
            timezone=settings.WEEKLY_REPORT_TIMEZONE,
        ),
        id="weekly_freelanceros_report",
        replace_existing=True,
    )

    scheduler.start()

    logger.info(
        "Weekly notifier started. Schedule: %s %02d:%02d %s",
        settings.WEEKLY_REPORT_DAY_OF_WEEK,
        settings.WEEKLY_REPORT_HOUR,
        settings.WEEKLY_REPORT_MINUTE,
        settings.WEEKLY_REPORT_TIMEZONE,
    )

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(run_scheduler())