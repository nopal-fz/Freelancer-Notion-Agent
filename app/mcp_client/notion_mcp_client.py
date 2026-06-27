import json
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.config import settings

# NotionMCPClient is a client for interacting with the FreelancerOS Notion MCP Server
class NotionMCPClient:
    def __init__(self) -> None:
        self.server_url = settings.MCP_NOTION_SERVER_URL

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with streamablehttp_client(self.server_url) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                result = await session.call_tool(
                    tool_name,
                    arguments=arguments or {},
                )

                return self._parse_tool_result(result)

    def _parse_tool_result(self, result: Any) -> dict[str, Any]:
        structured_content = getattr(result, "structuredContent", None)
        if structured_content:
            return structured_content

        if not result.content:
            return {
                "success": False,
                "message": "Empty MCP response.",
                "data": None,
            }

        first_content = result.content[0]
        text = getattr(first_content, "text", None)

        if not text:
            return {
                "success": False,
                "message": "Unsupported MCP response format.",
                "data": None,
            }

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "success": True,
                "message": "Raw MCP text response.",
                "data": text,
            }

    async def get_tasks(
        self,
        status: str | None = None,
        page_size: int = 10,
    ) -> dict[str, Any]:
        return await self.call_tool(
            "get_tasks",
            {
                "status": status,
                "page_size": page_size,
            },
        )

    async def create_task(
        self,
        task_name: str,
        status: str,
        category: str,
        due_date: str | None,
        priority: str,
        task_type: list[str] | None,
        effort_level: str,
        description: str | None,
        price: float,
        dp: float,
    ) -> dict[str, Any]:
        return await self.call_tool(
            "create_task",
            {
                "task_name": task_name,
                "status": status,
                "category": category,
                "due_date": due_date,
                "priority": priority,
                "task_type": task_type,
                "effort_level": effort_level,
                "description": description,
                "price": price,
                "dp": dp,
            },
        )

    async def calculate_receivables(
        self,
        statuses: list[str] | None = None
    ) -> dict[str, Any]:
        return await self.call_tool(
            "calculate_receivables",
            {
                "statuses": statuses
            },
        )
        
    async def task_statistics(self) -> dict[str, Any]:
        return await self.call_tool(
            "task_statistics",
            {},
        )

    async def weekly_summary(self) -> dict[str, Any]:
        return await self.call_tool(
            "weekly_summary",
            {},
        )
        
    async def recommend_today_focus(
        self,
        limit: int = 5,
    ) -> dict[str, Any]:
        return await self.call_tool(
            "recommend_today_focus",
            {
                "limit": limit,
            },
        )