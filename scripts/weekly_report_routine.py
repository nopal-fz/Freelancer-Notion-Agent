import asyncio

from app.scheduler.weekly_notifier import send_weekly_report_to_all_users

if __name__ == "__main__":
    asyncio.run(send_weekly_report_to_all_users())