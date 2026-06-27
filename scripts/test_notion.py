from app.services.notion_service import NotionService

# Scripts test connection to Notion API and prints database schema and sample tasks
def main() -> None:
    notion = NotionService()

    print("Checking Notion database schema...")
    schema = notion.get_database_schema()

    print("\nDatabase title:")
    title_items = schema.get("title", [])
    if title_items:
        print(title_items[0].get("plain_text"))
    else:
        print("(No title)")

    print("\nProperties:")
    for name, prop in schema.get("properties", {}).items():
        print(f"- {name}: {prop.get('type')}")

    print("\nFetching tasks...")
    tasks = notion.get_tasks(page_size=5)

    for index, task in enumerate(tasks, start=1):
        print(
            f"{index}. {task['task_name']} | "
            f"Status: {task['status']} | "
            f"Due: {task['due_date']} | "
            f"Priority: {task['priority']}"
        )


if __name__ == "__main__":
    main()