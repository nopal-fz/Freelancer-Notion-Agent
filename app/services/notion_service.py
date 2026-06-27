import logging
from typing import Any

from notion_client import Client

from app.config import settings

logger = logging.getLogger(__name__)

# Mapping of Notion database fields to their corresponding property names
NOTION_FIELDS = {
    "task_name": "Task name",
    "status": "Status",
    "category": "Category",
    "due_date": "Due date",
    "priority": "Priority",
    "task_type": "Task type",
    "effort_level": "Effort level",
    "description": "Description",
    "updated_at": "Updated at",
    "price": "Price",
    "dp": "Dp",
    "price_to_be_paid": "Price to be Paid",
    "past_due": "Past due",
    "assignment": "Assignment",
}

NOTION_OPTIONS = {
    "status": {
        "not_started": "Not started",
        "in_progress": "In progress",
        "done": "Done",
        "under_review": "Under review",
    },
    "category": {
        "individual": "Individual",
        "group": "Group",
    },
    "priority": {
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    },
    "task_type": {
        "bug": "🐞 Bug",
        "feature_request": "💬 Feature request",
        "polish": "📈 Polish",
        "self": "🦾 Self",
        "learn": "🏫Learn",
        "tech": "👨🏿‍💻 Tech",
    },
    "effort_level": {
        "small": "Small",
        "medium": "Medium",
        "large": "large",
    },
}

# NotionService class to interact with the Notion API
class NotionService:
    def __init__(self) -> None:
        if not settings.NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY is not configured.")

        if not settings.NOTION_DATABASE_ID:
            raise ValueError("NOTION_DATABASE_ID is not configured.")

        self.client = Client(auth=settings.NOTION_API_KEY)
        self.database_id = settings.NOTION_DATABASE_ID
        self.data_source_id = self._get_data_source_id()

    def _get_data_source_id(self) -> str:
        database = self.client.databases.retrieve(
            database_id=self.database_id,
        )

        data_sources = database.get("data_sources", [])

        if not data_sources:
            raise ValueError(
                "No data_sources found. Pastikan ID yang dipakai adalah database asli, "
                "bukan linked database/view."
            )

        return data_sources[0]["id"]

    def get_database_schema(self) -> dict[str, Any]:
        return self.client.data_sources.retrieve(
            data_source_id=self.data_source_id,
        )
    
    def get_tasks(
        self,
        page_size: int = 10,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch tasks from Notion with pagination.

        page_size here means total maximum tasks to return.
        Notion API only allows up to 100 results per request,
        so this function automatically paginates when page_size > 100.
        """

        all_results = []
        next_cursor = None

        while len(all_results) < page_size:
            remaining = page_size - len(all_results)
            batch_size = min(remaining, 100)

            query_payload = {
                "data_source_id": self.data_source_id,
                "page_size": batch_size,
                "sorts": [
                    {
                        "property": NOTION_FIELDS["due_date"],
                        "direction": "ascending",
                    }
                ],
            }

            if next_cursor:
                query_payload["start_cursor"] = next_cursor

            if status:
                query_payload["filter"] = {
                    "property": NOTION_FIELDS["status"],
                    "status": {
                        "equals": status,
                    },
                }

            response = self.client.data_sources.query(**query_payload)

            results = response.get("results", [])
            all_results.extend(results)

            has_more = response.get("has_more", False)
            next_cursor = response.get("next_cursor")

            if not has_more or not next_cursor:
                break

        return [self._parse_task(page) for page in all_results]

    def create_task(
        self,
        task_name: str,
        status: str = NOTION_OPTIONS["status"]["not_started"],
        category: str | None = None,
        due_date: str | None = None,
        priority: str | None = NOTION_OPTIONS["priority"]["medium"],
        task_type: list[str] | None = None,
        effort_level: str | None = None,
        description: str | None = None,
        price: float | None = 0,
        dp: float | None = 0,
    ) -> dict[str, Any]:
        properties = {
            NOTION_FIELDS["task_name"]: {
                "title": [
                    {
                        "text": {
                            "content": task_name,
                        }
                    }
                ]
            },
            NOTION_FIELDS["status"]: {
                "status": {
                    "name": status,
                }
            },
        }

        if category:
            properties[NOTION_FIELDS["category"]] = {
                "select": {
                    "name": category,
                }
            }

        if due_date:
            properties[NOTION_FIELDS["due_date"]] = {
                "date": {
                    "start": due_date,
                }
            }

        if priority:
            properties[NOTION_FIELDS["priority"]] = {
                "select": {
                    "name": priority,
                }
            }

        if task_type:
            properties[NOTION_FIELDS["task_type"]] = {
                "multi_select": [
                    {"name": item}
                    for item in task_type
                ]
            }

        if effort_level:
            properties[NOTION_FIELDS["effort_level"]] = {
                "select": {
                    "name": effort_level,
                }
            }

        if description:
            properties[NOTION_FIELDS["description"]] = {
                "rich_text": [
                    {
                        "text": {
                            "content": description,
                        }
                    }
                ]
            }

        if price is not None:
            properties[NOTION_FIELDS["price"]] = {
                "number": float(price),
            }

        if dp is not None:
            properties[NOTION_FIELDS["dp"]] = {
                "number": float(dp),
            }

        response = self.client.pages.create(
            parent={
                "data_source_id": self.data_source_id,
            },
            properties=properties,
        )

        return self._parse_task(response)

    def _parse_task(self, page: dict[str, Any]) -> dict[str, Any]:
        properties = page.get("properties", {})

        return {
            "id": page.get("id"),
            "task_name": self._get_title(properties, NOTION_FIELDS["task_name"]),
            "status": self._get_status(properties, NOTION_FIELDS["status"]),
            "category": self._get_select(properties, NOTION_FIELDS["category"]),
            "due_date": self._get_date(properties, NOTION_FIELDS["due_date"]),
            "priority": self._get_select(properties, NOTION_FIELDS["priority"]),
            "task_type": self._get_multi_select(properties, NOTION_FIELDS["task_type"]),
            "effort_level": self._get_select(properties, NOTION_FIELDS["effort_level"]),
            "description": self._get_rich_text(properties, NOTION_FIELDS["description"]),
            "updated_at": self._get_last_edited_time(
                properties,
                NOTION_FIELDS["updated_at"],
            ),
            "price": self._get_number(properties, NOTION_FIELDS["price"]),
            "dp": self._get_number(properties, NOTION_FIELDS["dp"]),
            "price_to_be_paid": self._get_formula_number(
                properties,
                NOTION_FIELDS["price_to_be_paid"],
            ),
            "url": page.get("url"),
        }

    def _get_title(self, properties: dict[str, Any], field_name: str) -> str | None:
        title_items = properties.get(field_name, {}).get("title", [])
        if not title_items:
            return None
        return title_items[0].get("plain_text")

    def _get_status(self, properties: dict[str, Any], field_name: str) -> str | None:
        status_value = properties.get(field_name, {}).get("status")
        if not status_value:
            return None
        return status_value.get("name")

    def _get_select(self, properties: dict[str, Any], field_name: str) -> str | None:
        select_value = properties.get(field_name, {}).get("select")
        if not select_value:
            return None
        return select_value.get("name")

    def _get_multi_select(self, properties: dict[str, Any], field_name: str) -> list[str]:
        values = properties.get(field_name, {}).get("multi_select", [])
        return [item.get("name") for item in values if item.get("name")]

    def _get_date(self, properties: dict[str, Any], field_name: str) -> str | None:
        date_value = properties.get(field_name, {}).get("date")
        if not date_value:
            return None
        return date_value.get("start")

    def _get_number(self, properties: dict[str, Any], field_name: str) -> float:
        value = properties.get(field_name, {}).get("number")
        return float(value or 0)

    def _get_formula_number(self, properties: dict[str, Any], field_name: str) -> float:
        formula_value = properties.get(field_name, {}).get("formula")

        if not formula_value:
            return 0.0

        if formula_value.get("type") == "number":
            return float(formula_value.get("number") or 0)

        return 0.0

    def _get_rich_text(self, properties: dict[str, Any], field_name: str) -> str | None:
        text_items = properties.get(field_name, {}).get("rich_text", [])
        if not text_items:
            return None
        return text_items[0].get("plain_text")

    def _get_last_edited_time(
        self,
        properties: dict[str, Any],
        field_name: str,
    ) -> str | None:
        return properties.get(field_name, {}).get("last_edited_time")