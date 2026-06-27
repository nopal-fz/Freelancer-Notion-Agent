from typing import Any
from datetime import date, datetime, timedelta
from mcp.server.fastmcp import FastMCP

from app.services.notion_service import (
    NotionService,
    NOTION_OPTIONS,
)
from app.services.priority_engine import recommend_today_tasks
from app.services.data_parser import parse_due_date

mcp = FastMCP(
    name="FreelancerOS Notion MCP Server",
    stateless_http=True,
    json_response=True,
)

def notion_service() -> NotionService:
    return NotionService()


def format_success(data: Any, message: str = "Success") -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data,
    }

def format_error(error: Exception) -> dict[str, Any]:
    return {
        "success": False,
        "message": str(error),
        "data": None,
    }

@mcp.tool()
def server_health() -> dict[str, Any]:
    """
    Check whether the FreelancerOS Notion MCP Server is running.
    """
    return {
        "success": True,
        "message": "FreelancerOS Notion MCP Server is running.",
        "data": {
            "server": "notion-mcp",
            "status": "ok",
        },
    }

@mcp.tool()
def get_tasks(
    status: str | None = None,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    Get tasks from the Notion freelancer tracker.

    Args:
        status: Optional task status filter.
                Supported values:
                Not started, In progress, Done, Under review.
        page_size: Maximum number of tasks to return.
    """
    try:
        notion = notion_service()
        tasks = notion.get_tasks(
            page_size=page_size,
            status=status,
        )

        return format_success(
            data=tasks,
            message="Tasks fetched successfully.",
        )

    except Exception as error:
        return format_error(error)

@mcp.tool()
def create_task(
    task_name: str,
    status: str = NOTION_OPTIONS["status"]["not_started"],
    category: str = NOTION_OPTIONS["category"]["individual"],
    due_date: str | None = None,
    priority: str = NOTION_OPTIONS["priority"]["medium"],
    task_type: list[str] | None = None,
    effort_level: str = NOTION_OPTIONS["effort_level"]["medium"],
    description: str | None = None,
    price: float = 0,
    dp: float = 0,
) -> dict[str, Any]:
    """
    Create a new freelancer task in Notion.

    Args:
        task_name: Task title.
        status: Task status. Example: Not started.
        category: Task category. Example: Individual or Group.
        due_date: Due date in ISO format, for example 2026-06-28.
        priority: Priority value. Example: High, Medium, Low.
        task_type: List of task types. Example: ["👨‍💻 Tech", "🧮 Learn"].
        effort_level: Effort value. Example: Small, Medium, large.
        description: Task description.
        price: Total project/task price.
        dp: Down payment received.
    """
    try:
        notion = notion_service()

        task = notion.create_task(
            task_name=task_name,
            status=status,
            category=category,
            due_date=due_date,
            priority=priority,
            task_type=task_type,
            effort_level=effort_level,
            description=description,
            price=price,
            dp=dp,
        )

        return format_success(
            data=task,
            message="Task created successfully.",
        )

    except Exception as error:
        return format_error(error)

@mcp.tool()
def calculate_receivables(
    statuses: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate total outstanding payment from Notion tasks.

    Default business rule:
    Calculate receivables from active tasks:
    - In progress
    - Under review

    Args:
        statuses: List of task statuses to calculate receivables from.
                  Example: ["In progress", "Under review"]
    """
    try:
        notion = notion_service()

        if not statuses:
            statuses = [
                NOTION_OPTIONS["status"]["in_progress"],
                NOTION_OPTIONS["status"]["under_review"],
            ]

        all_unpaid_tasks = []
        total_receivables = 0.0

        for status in statuses:
            tasks = notion.get_tasks(
                page_size=1000,
                status=status,
            )

            for task in tasks:
                price_to_be_paid = float(task.get("price_to_be_paid") or 0)

                if price_to_be_paid > 0:
                    total_receivables += price_to_be_paid
                    all_unpaid_tasks.append(
                        {
                            "task_name": task.get("task_name"),
                            "status": task.get("status"),
                            "due_date": task.get("due_date"),
                            "price": task.get("price"),
                            "dp": task.get("dp"),
                            "price_to_be_paid": price_to_be_paid,
                        }
                    )

        data = {
            "status_filters": statuses,
            "total_receivables": total_receivables,
            "unpaid_task_count": len(all_unpaid_tasks),
            "unpaid_tasks": all_unpaid_tasks,
        }

        return format_success(
            data=data,
            message=f"Receivables calculated successfully for statuses: {statuses}.",
        )

    except Exception as error:
        return format_error(error)
    
@mcp.tool()
def task_statistics() -> dict[str, Any]:
    """
    Generate task statistics from Notion.

    Returns:
    - total task count
    - count by status
    - count by priority
    - count by category
    """
    try:
        notion = notion_service()
        tasks = notion.get_tasks(page_size=1000)

        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}
        by_category: dict[str, int] = {}

        for task in tasks:
            status = task.get("status") or "Unknown"
            priority = task.get("priority") or "Unknown"
            category = task.get("category") or "Unknown"

            by_status[status] = by_status.get(status, 0) + 1
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1

        data = {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
        }

        return format_success(
            data=data,
            message="Task statistics generated successfully.",
        )

    except Exception as error:
        return format_error(error)


@mcp.tool()
def weekly_summary() -> dict[str, Any]:
    """
    Generate a weekly freelancer snapshot report.

    Note:
    This is a current snapshot report, not true weekly completion tracking,
    because the Notion database does not have a Completed At field yet.
    """
    try:
        notion = notion_service()

        all_tasks = notion.get_tasks(page_size=1000)
        in_progress_tasks = notion.get_tasks(
            page_size=1000,
            status=NOTION_OPTIONS["status"]["in_progress"],
        )
        not_started_tasks = notion.get_tasks(
            page_size=1000,
            status=NOTION_OPTIONS["status"]["not_started"],
        )
        done_tasks = notion.get_tasks(
            page_size=1000,
            status=NOTION_OPTIONS["status"]["done"],
        )
        under_review_tasks = notion.get_tasks(
            page_size=1000,
            status=NOTION_OPTIONS["status"]["under_review"],
        )

        overdue_tasks = []
        upcoming_deadlines = []

        today = date.today()
        next_7_days = today + timedelta(days=7)

        for task in all_tasks:
            due_date_value = task.get("due_date")

            if not due_date_value:
                continue

            try:
                due_date = datetime.fromisoformat(due_date_value).date()
            except ValueError:
                continue

            if due_date < today and task.get("status") != NOTION_OPTIONS["status"]["done"]:
                overdue_tasks.append(task)

            if today <= due_date <= next_7_days:
                upcoming_deadlines.append(task)

        receivable_result = calculate_receivables(
            statuses=[
                NOTION_OPTIONS["status"]["in_progress"],
                NOTION_OPTIONS["status"]["under_review"],
            ],
        )
        receivable_data = receivable_result.get("data") or {}

        data = {
            "summary_type": "current_week_snapshot",
            "total_tasks": len(all_tasks),
            "tasks_completed": len(done_tasks),
            "tasks_active": len(in_progress_tasks),
            "tasks_not_started": len(not_started_tasks),
            "tasks_under_review": len(under_review_tasks),
            "tasks_overdue": len(overdue_tasks),
            "outstanding_payments": receivable_data.get("total_receivables", 0),
            "upcoming_deadlines": [
                {
                    "task_name": task.get("task_name"),
                    "status": task.get("status"),
                    "due_date": task.get("due_date"),
                    "priority": task.get("priority"),
                }
                for task in upcoming_deadlines[:10]
            ],
            "recommended_focus": [
                "Selesaikan task overdue terlebih dahulu.",
                "Prioritaskan task In progress dengan deadline paling dekat.",
                "Follow up pembayaran untuk task yang masih memiliki sisa bayar.",
            ],
        }

        return format_success(
            data=data,
            message="Weekly summary generated successfully.",
        )

    except Exception as error:
        return format_error(error)

@mcp.tool()
def recommend_today_focus(
    limit: int = 5,
) -> dict[str, Any]:
    """
    Recommend tasks to focus on today using priority scoring.

    The score considers:
    - priority
    - task status
    - deadline urgency
    - effort level
    - outstanding payment
    """
    try:
        notion = notion_service()

        tasks = notion.get_tasks(page_size=1000)

        recommendations = recommend_today_tasks(
            tasks=tasks,
            limit=limit,
        )

        data = {
            "recommendation_type": "today_focus",
            "limit": limit,
            "tasks": recommendations,
        }

        return format_success(
            data=data,
            message="Today focus recommendation generated successfully.",
        )

    except Exception as error:
        return format_error(error)
    
@mcp.tool()
def search_tasks(
    query: str,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    Search tasks by task name keyword.
    """
    try:
        notion = notion_service()

        tasks = notion.search_tasks(
            query=query,
            page_size=page_size,
        )

        return format_success(
            data=tasks,
            message="Tasks searched successfully.",
        )

    except Exception as error:
        return format_error(error)
    
@mcp.tool()
def update_task(
    query: str,
    status: str | None = None,
    category: str | None = None,
    due_date: str | None = None,
    priority: str | None = None,
    task_type: list[str] | None = None,
    effort_level: str | None = None,
    description: str | None = None,
    price: float | None = None,
    dp: float | None = None,
) -> dict[str, Any]:
    """
    Update a task by searching task name.

    If exactly one task matches, update it.
    If multiple tasks match, return candidate tasks and ask user to be more specific.
    """
    try:
        notion = notion_service()

        matches = notion.search_tasks(
            query=query,
            page_size=10,
        )

        if not matches:
            return {
                "success": False,
                "message": f"Tidak ada task yang cocok dengan query: {query}",
                "data": {
                    "matches": [],
                },
            }

        if len(matches) > 1:
            return {
                "success": False,
                "message": (
                    "Ditemukan lebih dari satu task yang cocok. "
                    "Mohon gunakan nama task yang lebih spesifik."
                ),
                "data": {
                    "matches": [
                        {
                            "id": task.get("id"),
                            "task_name": task.get("task_name"),
                            "status": task.get("status"),
                            "due_date": task.get("due_date"),
                        }
                        for task in matches
                    ],
                },
            }

        task = matches[0]

        parsed_due_date = parse_due_date(due_date)

        updated_task = notion.update_task(
            task_id=task["id"],
            status=status,
            category=category,
            due_date=parsed_due_date,
            priority=priority,
            task_type=task_type,
            effort_level=effort_level,
            description=description,
            price=price,
            dp=dp,
        )

        return format_success(
            data=updated_task,
            message="Task updated successfully.",
        )

    except Exception as error:
        return format_error(error)

if __name__ == "__main__":
    mcp.settings.host = "127.0.0.1"
    mcp.settings.port = 8101
    mcp.run(transport="streamable-http")