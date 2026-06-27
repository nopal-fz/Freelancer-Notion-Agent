import json
import logging
from typing import Any

from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from app.agent.prompts import INTENT_CLASSIFIER_PROMPT
from app.agent.state import AgentState
from app.config import settings
from app.mcp_client.notion_mcp_client import NotionMCPClient
from app.telegram.commands import (
    format_tasks,
    format_rupiah,
)

logger = logging.getLogger(__name__)


def get_llm() -> ChatGroq:
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")

    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0,
    )


def safe_json_loads(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise

        return json.loads(text[start : end + 1])


async def classify_intent(state: AgentState) -> AgentState:
    llm = get_llm()

    messages = [
        ("system", INTENT_CLASSIFIER_PROMPT),
        ("human", state["user_message"]),
    ]

    response = await llm.ainvoke(messages)
    content = response.content

    parsed = safe_json_loads(str(content))

    return {
        **state,
        "intent": parsed.get("intent"),
        "arguments": parsed.get("arguments") or {},
    }


async def execute_intent(state: AgentState) -> AgentState:
    intent = state.get("intent")
    arguments = state.get("arguments") or {}

    mcp_client = NotionMCPClient()

    try:
        if intent == "get_tasks":
            result = await mcp_client.get_tasks(
                status=arguments.get("status"),
                page_size=int(arguments.get("page_size") or 10),
            )

        elif intent == "create_task":
            task_name = arguments.get("task_name")

            if not task_name:
                return {
                    **state,
                    "tool_result": None,
                    "error": "Task name belum terdeteksi.",
                }

            result = await mcp_client.create_task(
                task_name=task_name,
                status=arguments.get("status") or "Not started",
                category=arguments.get("category") or "Individual",
                due_date=arguments.get("due_date"),
                priority=arguments.get("priority") or "Medium",
                task_type=arguments.get("task_type") or ["👨‍💻 Tech"],
                effort_level=arguments.get("effort_level") or "Medium",
                description=arguments.get("description")
                or "Task ini dibuat dari natural language melalui FreelancerOS Agent.",
                price=float(arguments.get("price") or 0),
                dp=float(arguments.get("dp") or 0),
            )
            
        elif intent == "calculate_receivables":
            result = await mcp_client.calculate_receivables(
                statuses=arguments.get("statuses")
                or [
                    "In progress",
                    "Under review",
                ],
            )

        elif intent == "task_statistics":
            result = await mcp_client.task_statistics()

        elif intent == "weekly_summary":
            result = await mcp_client.weekly_summary()
            
        elif intent == "recommend_today_focus":
            result = await mcp_client.recommend_today_focus(
                limit=int(arguments.get("limit") or 5),
            )

        else:
            return {
                **state,
                "tool_result": None,
                "error": "Intent belum dikenali.",
            }

        return {
            **state,
            "tool_result": result,
            "error": None,
        }

    except Exception as error:
        logger.exception("Failed to execute intent.")
        return {
            **state,
            "tool_result": None,
            "error": str(error),
        }


def format_receivables(data: dict[str, Any]) -> str:
    unpaid_tasks = data.get("unpaid_tasks") or []
    status_filters = data.get("status_filters") or []

    lines = [
        "💰 Piutang Aktif",
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


def format_statistics(data: dict[str, Any]) -> str:
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


def format_weekly_summary(data: dict[str, Any]) -> str:
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

    return "\n".join(lines)

def format_today_focus(data: dict[str, Any]) -> str:
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

async def format_response(state: AgentState) -> AgentState:
    if state.get("error"):
        return {
            **state,
            "final_response": (
                "Maaf, aku belum bisa memproses pesan itu.\n\n"
                f"Detail: {state.get('error')}\n\n"
                "Coba pakai /help untuk melihat command yang tersedia."
            ),
        }

    intent = state.get("intent")
    tool_result = state.get("tool_result") or {}

    if not tool_result.get("success"):
        return {
            **state,
            "final_response": (
                "Tool MCP gagal dijalankan.\n\n"
                f"Error: {tool_result.get('message')}"
            ),
        }

    data = tool_result.get("data")

    if intent == "get_tasks":
        return {
            **state,
            "final_response": format_tasks(data or []),
        }

    if intent == "create_task":
        task = data or {}
        task_type = task.get("task_type") or []

        if isinstance(task_type, list):
            task_type_text = ", ".join(task_type) if task_type else "-"
        else:
            task_type_text = str(task_type)

        return {
            **state,
            "final_response": (
                "✅ Task baru berhasil dibuat lewat Agent + MCP.\n\n"
                f"Task: {task.get('task_name')}\n"
                f"Status: {task.get('status')}\n"
                f"Deadline: {task.get('due_date')}\n"
                f"Priority: {task.get('priority')}\n"
                f"Task type: {task_type_text}\n"
                f"Price: {format_rupiah(task.get('price'))}\n"
                f"DP: {format_rupiah(task.get('dp'))}\n"
                f"Sisa bayar: {format_rupiah(task.get('price_to_be_paid'))}"
            ),
        }

    if intent == "calculate_receivables":
        return {
            **state,
            "final_response": format_receivables(data or {}),
        }

    if intent == "task_statistics":
        return {
            **state,
            "final_response": format_statistics(data or {}),
        }

    if intent == "weekly_summary":
        return {
            **state,
            "final_response": format_weekly_summary(data or {}),
        }
        
    if intent == "recommend_today_focus":
        return {
            **state,
            "final_response": format_today_focus(data or {}),
        }

    return {
        **state,
        "final_response": "Aku belum paham maksudnya. Coba pakai /help dulu ya.",
    }


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("execute_intent", execute_intent)
    graph.add_node("format_response", format_response)

    graph.set_entry_point("classify_intent")
    graph.add_edge("classify_intent", "execute_intent")
    graph.add_edge("execute_intent", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()


agent_graph = build_agent_graph()


async def run_freelanceros_agent(user_message: str) -> str:
    initial_state: AgentState = {
        "user_message": user_message,
        "intent": None,
        "arguments": {},
        "tool_result": None,
        "final_response": None,
        "error": None,
    }

    result = await agent_graph.ainvoke(initial_state)

    return result.get("final_response") or "Aku belum bisa membuat respons."