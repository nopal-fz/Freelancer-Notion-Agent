from datetime import date, datetime
from typing import Any


PRIORITY_WEIGHT = {
    "High": 35,
    "Medium": 20,
    "Low": 10,
}


STATUS_WEIGHT = {
    "In progress": 20,
    "Under review": 15,
    "Not started": 10,
    "Done": -100,
}


EFFORT_WEIGHT = {
    "Small": 15,
    "Medium": 10,
    "large": 5,
    "Large": 5,
}


def parse_due_date(value: str | None) -> date | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def calculate_deadline_score(due_date_value: str | None) -> tuple[int, str]:
    due_date = parse_due_date(due_date_value)

    if not due_date:
        return 0, "tidak ada deadline"

    today = date.today()
    days_left = (due_date - today).days

    if days_left < 0:
        return 45, "deadline sudah lewat"
    if days_left == 0:
        return 40, "deadline hari ini"
    if days_left <= 2:
        return 35, "deadline sangat dekat"
    if days_left <= 7:
        return 25, "deadline minggu ini"

    return 10, "deadline masih cukup jauh"


def calculate_receivable_score(price_to_be_paid: float | int | None) -> tuple[int, str | None]:
    value = float(price_to_be_paid or 0)

    if value > 0:
        return 5, "masih ada sisa pembayaran"

    return 0, None


def calculate_task_priority_score(task: dict[str, Any]) -> dict[str, Any]:
    status = task.get("status") or "Not started"
    priority = task.get("priority") or "Medium"
    effort_level = task.get("effort_level") or "Medium"
    due_date = task.get("due_date")
    price_to_be_paid = task.get("price_to_be_paid") or 0

    score = 0
    reasons = []

    priority_score = PRIORITY_WEIGHT.get(priority, 10)
    score += priority_score
    reasons.append(f"priority {priority}")

    status_score = STATUS_WEIGHT.get(status, 0)
    score += status_score
    reasons.append(f"status {status}")

    effort_score = EFFORT_WEIGHT.get(effort_level, 10)
    score += effort_score

    if effort_level == "Small":
        reasons.append("effort kecil, cocok jadi quick win")
    elif effort_level == "Medium":
        reasons.append("effort sedang")
    else:
        reasons.append("effort besar")

    deadline_score, deadline_reason = calculate_deadline_score(due_date)
    score += deadline_score
    reasons.append(deadline_reason)

    receivable_score, receivable_reason = calculate_receivable_score(price_to_be_paid)
    score += receivable_score

    if receivable_reason:
        reasons.append(receivable_reason)

    return {
        **task,
        "priority_score": score,
        "priority_reasons": reasons,
    }


def recommend_today_tasks(
    tasks: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    active_tasks = [
        task
        for task in tasks
        if task.get("status") != "Done"
    ]

    scored_tasks = [
        calculate_task_priority_score(task)
        for task in active_tasks
    ]

    return sorted(
        scored_tasks,
        key=lambda task: task.get("priority_score", 0),
        reverse=True,
    )[:limit]