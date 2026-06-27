from datetime import date, timedelta

from app.mcp_client.notion_mcp_client import NotionMCPClient
from app.services.notion_service import NOTION_OPTIONS


STATUS_ALIASES = {
    "not started": NOTION_OPTIONS["status"]["not_started"],
    "not_started": NOTION_OPTIONS["status"]["not_started"],
    "todo": NOTION_OPTIONS["status"]["not_started"],
    "to do": NOTION_OPTIONS["status"]["not_started"],

    "in progress": NOTION_OPTIONS["status"]["in_progress"],
    "progress": NOTION_OPTIONS["status"]["in_progress"],
    "ongoing": NOTION_OPTIONS["status"]["in_progress"],

    "done": NOTION_OPTIONS["status"]["done"],
    "selesai": NOTION_OPTIONS["status"]["done"],

    "under review": NOTION_OPTIONS["status"]["under_review"],
    "review": NOTION_OPTIONS["status"]["under_review"],
}


CATEGORY_ALIASES = {
    "individual": NOTION_OPTIONS["category"]["individual"],
    "individu": NOTION_OPTIONS["category"]["individual"],
    "group": NOTION_OPTIONS["category"]["group"],
    "kelompok": NOTION_OPTIONS["category"]["group"],
}


PRIORITY_ALIASES = {
    "high": NOTION_OPTIONS["priority"]["high"],
    "tinggi": NOTION_OPTIONS["priority"]["high"],
    "medium": NOTION_OPTIONS["priority"]["medium"],
    "sedang": NOTION_OPTIONS["priority"]["medium"],
    "low": NOTION_OPTIONS["priority"]["low"],
    "rendah": NOTION_OPTIONS["priority"]["low"],
}


TASK_TYPE_ALIASES = {
    "bug": NOTION_OPTIONS["task_type"]["bug"],
    "feature": NOTION_OPTIONS["task_type"]["feature_request"],
    "feature request": NOTION_OPTIONS["task_type"]["feature_request"],
    "polish": NOTION_OPTIONS["task_type"]["polish"],
    "self": NOTION_OPTIONS["task_type"]["self"],
    "learn": NOTION_OPTIONS["task_type"]["learn"],
    "learning": NOTION_OPTIONS["task_type"]["learn"],
    "tech": NOTION_OPTIONS["task_type"]["tech"],
}


EFFORT_ALIASES = {
    "small": NOTION_OPTIONS["effort_level"]["small"],
    "kecil": NOTION_OPTIONS["effort_level"]["small"],
    "medium": NOTION_OPTIONS["effort_level"]["medium"],
    "sedang": NOTION_OPTIONS["effort_level"]["medium"],
    "large": NOTION_OPTIONS["effort_level"]["large"],
    "besar": NOTION_OPTIONS["effort_level"]["large"],
}


def format_rupiah(value: float | int | None) -> str:
    value = float(value or 0)
    return f"Rp {value:,.0f}".replace(",", ".")


def normalize_from_alias(
    value: str | None,
    aliases: dict[str, str],
    default: str | None = None,
) -> str | None:
    if not value:
        return default

    cleaned = value.strip().lower()
    return aliases.get(cleaned, value.strip())


def parse_money(value: str | None, default: float = 0) -> float:
    if not value:
        return default

    cleaned = (
        value.replace("Rp", "")
        .replace("rp", "")
        .replace(".", "")
        .replace(",", "")
        .strip()
    )

    if not cleaned:
        return default

    return float(cleaned)


def parse_key_value_payload(payload: str) -> dict[str, str]:
    result = {}

    parts = payload.split(";")

    for part in parts:
        if "=" not in part:
            continue

        key, value = part.split("=", 1)
        result[key.strip().lower()] = value.strip()

    return result


def parse_task_types(value: str | None) -> list[str] | None:
    if not value:
        return None

    items = [item.strip() for item in value.split(",") if item.strip()]

    if not items:
        return None

    return [
        normalize_from_alias(item, TASK_TYPE_ALIASES, default=item)
        for item in items
    ]


def extract_status_from_tasks_command(text: str) -> str | None:
    normalized = text.strip()

    shortcut_map = {
        "/tasks_progress": "progress",
        "/tasks_done": "done",
        "/tasks_review": "review",
        "/tasks_todo": "todo",
        "/tasks_not_started": "not started",
        "/tasks_in_progress": "in progress",
        "/tasks_under_review": "under review",
    }

    if normalized in shortcut_map:
        return normalize_from_alias(shortcut_map[normalized], STATUS_ALIASES)

    payload = normalized.replace("/tasks", "", 1).strip()

    if not payload:
        return None

    if payload.startswith("status="):
        status_value = payload.replace("status=", "", 1).strip()
        return normalize_from_alias(status_value, STATUS_ALIASES)

    return normalize_from_alias(payload, STATUS_ALIASES)


def format_tasks(tasks: list[dict], title: str = "📋 Task dari Notion") -> str:
    if not tasks:
        return "Belum ada task yang cocok dengan filter tersebut."

    lines = [f"{title}:\n"]

    for index, task in enumerate(tasks, start=1):
        task_name = task.get("task_name") or "(Tanpa nama)"
        status = task.get("status") or "-"
        due_date = task.get("due_date") or "-"
        priority = task.get("priority") or "-"
        category = task.get("category") or "-"
        task_type = task.get("task_type") or []
        effort_level = task.get("effort_level") or "-"
        price = task.get("price") or 0
        dp = task.get("dp") or 0
        price_to_be_paid = task.get("price_to_be_paid") or 0

        if isinstance(task_type, list):
            task_type_text = ", ".join(task_type) if task_type else "-"
        else:
            task_type_text = str(task_type)

        lines.append(
            f"{index}. {task_name}\n"
            f"Status: {status}\n"
            f"Category: {category}\n"
            f"Deadline: {due_date}\n"
            f"Priority: {priority}\n"
            f"Task type: {task_type_text}\n"
            f"Effort: {effort_level}\n"
            f"Price: {format_rupiah(price)}\n"
            f"DP: {format_rupiah(dp)}\n"
            f"Sisa bayar: {format_rupiah(price_to_be_paid)}\n"
        )

    return "\n".join(lines)


async def handle_tasks_command(text: str) -> str:
    mcp_client = NotionMCPClient()

    status = extract_status_from_tasks_command(text)
    result = await mcp_client.get_tasks(
        page_size=10,
        status=status,
    )

    if not result.get("success"):
        return f"Gagal mengambil task dari MCP Server.\n\nError: {result.get('message')}"

    tasks = result.get("data") or []

    if status:
        return format_tasks(
            tasks,
            title=f"📋 Task dengan status: {status}",
        )

    return format_tasks(tasks)


async def handle_add_command(text: str) -> str:
    payload = text.replace("/add", "", 1).strip()

    if not payload:
        return (
            "Format /add belum lengkap.\n\n"
            "Contoh simple:\n"
            "/add Belajar MCP Server\n\n"
            "Contoh lengkap:\n"
            "/add task=Belajar MCP Server; due=2026-06-28; status=Not started; category=Individual; priority=High; type=Tech,Learn; effort=Medium; price=250000; dp=50000; desc=Belajar dasar MCP"
        )

    if "task=" in payload:
        data = parse_key_value_payload(payload)

        task_name = data.get("task")
        if not task_name:
            return "Field task wajib diisi. Contoh: task=Belajar MCP Server"

        due_date = data.get("due") or (date.today() + timedelta(days=3)).isoformat()

        status = normalize_from_alias(
            data.get("status"),
            STATUS_ALIASES,
            default=NOTION_OPTIONS["status"]["not_started"],
        )

        category = normalize_from_alias(
            data.get("category"),
            CATEGORY_ALIASES,
            default=NOTION_OPTIONS["category"]["individual"],
        )

        priority = normalize_from_alias(
            data.get("priority"),
            PRIORITY_ALIASES,
            default=NOTION_OPTIONS["priority"]["medium"],
        )

        task_type = parse_task_types(data.get("type"))

        effort_level = normalize_from_alias(
            data.get("effort"),
            EFFORT_ALIASES,
            default=NOTION_OPTIONS["effort_level"]["medium"],
        )

        price = parse_money(data.get("price"), default=0)
        dp = parse_money(data.get("dp"), default=0)
        description = data.get("desc") or "Task ini dibuat dari Telegram melalui FreelancerOS."

    else:
        task_name = payload
        due_date = (date.today() + timedelta(days=3)).isoformat()
        status = NOTION_OPTIONS["status"]["not_started"]
        category = NOTION_OPTIONS["category"]["individual"]
        priority = NOTION_OPTIONS["priority"]["medium"]
        task_type = [NOTION_OPTIONS["task_type"]["tech"]]
        effort_level = NOTION_OPTIONS["effort_level"]["medium"]
        price = 0
        dp = 0
        description = "Task ini dibuat dari Telegram melalui FreelancerOS."

    mcp_client = NotionMCPClient()

    result = await mcp_client.create_task(
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

    if not result.get("success"):
        return f"Gagal membuat task lewat MCP Server.\n\nError: {result.get('message')}"

    task = result.get("data") or {}

    task_type_text = task.get("task_type") or []
    if isinstance(task_type_text, list):
        task_type_text = ", ".join(task_type_text) if task_type_text else "-"

    return (
        "✅ Task baru berhasil dibuat lewat MCP.\n\n"
        f"Task: {task.get('task_name')}\n"
        f"Status: {task.get('status')}\n"
        f"Category: {task.get('category')}\n"
        f"Deadline: {task.get('due_date')}\n"
        f"Priority: {task.get('priority')}\n"
        f"Task type: {task_type_text}\n"
        f"Effort: {task.get('effort_level')}\n"
        f"Price: {format_rupiah(task.get('price'))}\n"
        f"DP: {format_rupiah(task.get('dp'))}\n"
        f"Sisa bayar: {format_rupiah(task.get('price_to_be_paid'))}"
    )


async def handle_receivables_command(text: str = "/receivables") -> str:
    mcp_client = NotionMCPClient()

    normalized_text = text.strip()

    if normalized_text.startswith("/receivables_progress"):
        statuses = [
            NOTION_OPTIONS["status"]["in_progress"],
        ]
        title = "💰 Piutang In Progress"

    elif normalized_text.startswith("/receivables_review"):
        statuses = [
            NOTION_OPTIONS["status"]["under_review"],
        ]
        title = "💰 Piutang Under Review"

    else:
        statuses = [
            NOTION_OPTIONS["status"]["in_progress"],
            NOTION_OPTIONS["status"]["under_review"],
        ]
        title = "💰 Piutang Aktif"

    result = await mcp_client.calculate_receivables(
        statuses=statuses,
    )

    if not result.get("success"):
        return f"Gagal menghitung piutang lewat MCP Server.\n\nError: {result.get('message')}"

    data = result.get("data") or {}
    unpaid_tasks = data.get("unpaid_tasks") or []
    status_filters = data.get("status_filters") or []

    lines = [
        title,
        "",
        f"Status filter: {', '.join(status_filters)}",
        f"Total piutang: {format_rupiah(data.get('total_receivables'))}",
        f"Jumlah task belum lunas: {data.get('unpaid_task_count')}",
    ]

    if unpaid_tasks:
        lines.append("")
        lines.append("Rincian:")

        for index, task in enumerate(unpaid_tasks, start=1):
            lines.append(
                f"{index}. {task.get('task_name')}\n"
                f"Status: {task.get('status')}\n"
                f"Deadline: {task.get('due_date') or '-'}\n"
                f"Price: {format_rupiah(task.get('price'))}\n"
                f"DP: {format_rupiah(task.get('dp'))}\n"
                f"Sisa bayar: {format_rupiah(task.get('price_to_be_paid'))}"
            )

    return "\n".join(lines)


async def handle_stats_command() -> str:
    mcp_client = NotionMCPClient()

    result = await mcp_client.task_statistics()

    if not result.get("success"):
        return f"Gagal membuat statistik lewat MCP Server.\n\nError: {result.get('message')}"

    data = result.get("data") or {}

    lines = [
        "📊 FreelancerOS Task Statistics",
        "",
        f"Total tasks: {data.get('total_tasks', 0)}",
        "",
        "By Status:",
    ]

    for key, value in (data.get("by_status") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("By Priority:")
    for key, value in (data.get("by_priority") or {}).items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("By Category:")
    for key, value in (data.get("by_category") or {}).items():
        lines.append(f"- {key}: {value}")

    return "\n".join(lines)


async def handle_report_command() -> str:
    mcp_client = NotionMCPClient()

    result = await mcp_client.weekly_summary()

    if not result.get("success"):
        return f"Gagal membuat report lewat MCP Server.\n\nError: {result.get('message')}"

    data = result.get("data") or {}
    upcoming_deadlines = data.get("upcoming_deadlines") or []
    recommended_focus = data.get("recommended_focus") or []

    lines = [
        "📊 Weekly Freelancer Report",
        "",
        f"✅ Tasks Completed: {data.get('tasks_completed', 0)}",
        f"🟡 Tasks Active: {data.get('tasks_active', 0)}",
        f"⚪ Tasks Not Started: {data.get('tasks_not_started', 0)}",
        f"🧪 Tasks Under Review: {data.get('tasks_under_review', 0)}",
        f"🔴 Tasks Overdue: {data.get('tasks_overdue', 0)}",
        "",
        f"🧾 Outstanding Payments: {format_rupiah(data.get('outstanding_payments'))}",
        "",
        "📅 Upcoming Deadlines:",
    ]

    if upcoming_deadlines:
        for index, task in enumerate(upcoming_deadlines, start=1):
            lines.append(
                f"{index}. {task.get('task_name')} — {task.get('due_date')} "
                f"({task.get('priority')})"
            )
    else:
        lines.append("- Tidak ada deadline dalam 7 hari ke depan.")

    lines.append("")
    lines.append("🎯 Recommended Focus:")

    for index, focus in enumerate(recommended_focus, start=1):
        lines.append(f"{index}. {focus}")

    lines.append("")
    lines.append(
        "Catatan: report ini masih berupa current snapshot. "
        "Agar completed task per minggu akurat, nanti tambahkan field Completed At."
    )

    return "\n".join(lines)


def handle_help_command() -> str:
    return (
        "🤖 FreelancerOS Command Helper\n\n"
        "Command utama:\n\n"
        "/help\n"
        "Menampilkan daftar command.\n\n"
        "/tasks\n"
        "Melihat semua task dari Notion lewat MCP.\n\n"
        "/tasks progress\n"
        "Melihat task dengan status In progress.\n\n"
        "/tasks done\n"
        "Melihat task dengan status Done.\n\n"
        "/tasks review\n"
        "Melihat task dengan status Under review.\n\n"
        "/tasks todo\n"
        "Melihat task dengan status Not started.\n\n"
        "Shortcut task:\n"
        "/tasks_progress\n"
        "/tasks_done\n"
        "/tasks_review\n"
        "/tasks_todo\n\n"
        "/add Nama task\n"
        "Menambahkan task simple lewat MCP.\n\n"
        "Format lengkap /add:\n"
        "/add task=Belajar MCP Server; due=2026-06-28; status=Not started; category=Individual; priority=High; type=Tech,Learn; effort=Medium; price=250000; dp=50000; desc=Belajar dasar MCP\n\n"
        "Finance command:\n\n"
        "/receivables\n"
        "Menghitung total piutang aktif dari task In progress + Under review.\n\n"
        "/receivables_active\n"
        "Menghitung piutang gabungan In progress + Under review.\n\n"
        "/receivables_progress\n"
        "Menghitung piutang dari task In progress saja.\n\n"
        "/receivables_review\n"
        "Menghitung piutang dari task Under review saja.\n\n"
        "Analytics command:\n\n"
        "/stats\n"
        "Melihat statistik task berdasarkan status, priority, dan category.\n\n"
        "/report\n"
        "Membuat weekly freelancer report.\n\n"
        "Natural language juga bisa, contoh:\n"
        "- task apa yang lagi progress?\n"
        "- berapa piutang aktif saya?\n"
        "- berapa piutang yang under review?\n"
        "- buat laporan minggu ini\n"
        "- tambah task belajar langgraph"
    )


async def handle_telegram_command(text: str) -> str:
    normalized_text = text.strip()

    if normalized_text.startswith("/tasks") or normalized_text.startswith("/tasks_"):
        return await handle_tasks_command(normalized_text)

    if normalized_text.startswith("/add"):
        return await handle_add_command(normalized_text)

    if normalized_text.startswith("/receivables"):
        return await handle_receivables_command(normalized_text)

    if normalized_text.startswith("/stats"):
        return await handle_stats_command()

    if normalized_text.startswith("/report"):
        return await handle_report_command()
    
    if normalized_text.startswith("/focus"):
        return await handle_focus_command()

    if normalized_text.startswith("/help") or normalized_text.startswith("/start"):
        return handle_help_command()

    return (
        "Command belum dikenali.\n\n"
        "Coba pakai:\n"
        "/help\n"
        "/tasks\n"
        "/tasks progress\n"
        "/add Nama task\n"
        "/receivables\n"
        "/stats\n"
        "/report"
    )
    
async def handle_focus_command() -> str:
    mcp_client = NotionMCPClient()

    result = await mcp_client.recommend_today_focus(limit=5)

    if not result.get("success"):
        return f"Gagal membuat rekomendasi fokus lewat MCP Server.\n\nError: {result.get('message')}"

    data = result.get("data") or {}
    tasks = data.get("tasks") or []

    if not tasks:
        return "Belum ada task aktif yang perlu direkomendasikan."

    lines = [
        "🎯 Rekomendasi Fokus Hari Ini",
        "",
    ]

    for index, task in enumerate(tasks, start=1):
        reasons = task.get("priority_reasons") or []
        reasons_text = ", ".join(reasons[:4])

        lines.append(
            f"{index}. {task.get('task_name')}\n"
            f"Score: {task.get('priority_score')}\n"
            f"Status: {task.get('status')}\n"
            f"Deadline: {task.get('due_date') or '-'}\n"
            f"Priority: {task.get('priority')}\n"
            f"Effort: {task.get('effort_level')}\n"
            f"Sisa bayar: {format_rupiah(task.get('price_to_be_paid'))}\n"
            f"Alasan: {reasons_text}\n"
        )

    lines.append("Saran: mulai dari task nomor 1, lalu lanjut task dengan effort paling kecil.")

    return "\n".join(lines)