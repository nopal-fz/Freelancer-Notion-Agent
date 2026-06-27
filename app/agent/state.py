from typing import Any, TypedDict

class AgentState(TypedDict):
    user_message: str
    intent: str | None
    arguments: dict[str, Any]
    tool_result: dict[str, Any] | None
    final_response: str | None
    error: str | None