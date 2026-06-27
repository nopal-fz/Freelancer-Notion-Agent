from datetime import date, timedelta


WEEKDAY_MAP = {
    "senin": 0,
    "monday": 0,
    "selasa": 1,
    "tuesday": 1,
    "rabu": 2,
    "wednesday": 2,
    "kamis": 3,
    "thursday": 3,
    "jumat": 4,
    "jum'at": 4,
    "friday": 4,
    "sabtu": 5,
    "saturday": 5,
    "minggu": 6,
    "ahad": 6,
    "sunday": 6,
}


def next_weekday(target_weekday: int, today: date | None = None) -> date:
    today = today or date.today()

    days_ahead = target_weekday - today.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    return today + timedelta(days=days_ahead)


def parse_due_date(value: str | None, today: date | None = None) -> str | None:
    """
    Parse simple Indonesian/English deadline text into ISO date.

    Supported:
    - YYYY-MM-DD
    - hari ini / today
    - besok / tomorrow
    - lusa
    - minggu depan / next week
    - nama hari: senin, selasa, rabu, kamis, jumat, sabtu, minggu
    """

    if not value:
        return None

    today = today or date.today()
    text = value.strip().lower()

    # Already ISO format
    try:
        parsed = date.fromisoformat(text)
        return parsed.isoformat()
    except ValueError:
        pass

    if text in ["hari ini", "today"]:
        return today.isoformat()

    if text in ["besok", "tomorrow"]:
        return (today + timedelta(days=1)).isoformat()

    if text in ["lusa"]:
        return (today + timedelta(days=2)).isoformat()

    if text in ["minggu depan", "next week"]:
        return (today + timedelta(days=7)).isoformat()

    # Handle phrases like:
    # "deadline jumat", "jumat depan", "hari jumat"
    for weekday_name, weekday_index in WEEKDAY_MAP.items():
        if weekday_name in text:
            return next_weekday(
                target_weekday=weekday_index,
                today=today,
            ).isoformat()

    return None