from datetime import date, timedelta

from app.services.notion_service import NotionService, NOTION_OPTIONS


def main() -> None:
    notion = NotionService()

    due_date = (date.today() + timedelta(days=3)).isoformat()

    task = notion.create_task(
        task_name="Test Task dari FreelancerOS",
        status=NOTION_OPTIONS["status"]["not_started"],
        category=NOTION_OPTIONS["category"]["individual"],
        due_date=due_date,
        priority=NOTION_OPTIONS["priority"]["medium"],
        task_type=[
            NOTION_OPTIONS["task_type"]["tech"],
            NOTION_OPTIONS["task_type"]["learn"],
        ],
        effort_level=NOTION_OPTIONS["effort_level"]["medium"],
        description="Task ini dibuat dari Python untuk test integrasi Notion.",
        price=100000,
        dp=25000,
    )

    print("Task created:")
    print(task)


if __name__ == "__main__":
    main()