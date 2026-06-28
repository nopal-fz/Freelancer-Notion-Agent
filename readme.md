# FreelancerOS AI Agent — Development Runbook

## Project Overview

FreelancerOS AI Agent adalah Telegram-based AI assistant untuk membantu freelancer mengelola task, project, deadline, pembayaran, dan laporan menggunakan Notion sebagai database utama dan MCP sebagai tool integration layer.

## Current Architecture

```text
Telegram Bot
→ FastAPI Webhook
→ Telegram Command Handler
→ MCP Client
→ Notion MCP Server
→ NotionService
→ Notion Database
```

## Main Components

```text
app/
├── main.py
├── config.py
├── telegram/
│   ├── webhook.py
│   ├── sender.py
│   └── commands.py
├── services/
│   └── notion_service.py
└── mcp_client/
    └── notion_mcp_client.py

mcp_servers/
└── notion_server/
    └── server.py

scripts/
├── set_webhook.py
├── set_bot_commands.py
├── test_notion.py
├── create_sample_task.py
└── inspect_notion_options.py
```

## Environment Variables

Create `.env`:

```env
APP_ENV=development
APP_NAME=FreelancerOS AI Agent

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_SECRET=freelanceros-secret-123
ALLOWED_TELEGRAM_USER_IDS=your_telegram_user_id

NOTION_API_KEY=your_notion_integration_secret
NOTION_DATABASE_ID=your_notion_database_id
NOTION_API_VERSION=2022-06-28

MCP_NOTION_SERVER_URL=http://127.0.0.1:8101/mcp
```

## How to Run Locally

### Terminal 1 — Run FastAPI

```bash
uvicorn app.main:app --reload
```

Check:

```text
http://127.0.0.1:8000/health
```

### Terminal 2 — Run ngrok

```bash
ngrok http 8000
```

Copy the HTTPS URL.

### Terminal 3 — Set Telegram Webhook

```bash
python -m scripts.set_webhook https://your-ngrok-url
```

### Terminal 4 — Run Notion MCP Server

```bash
python -m app.mcp_servers.notion_server.server
```

MCP server URL:

```text
http://127.0.0.1:8101/mcp
```

## Set Telegram Bot Commands

```bash
python -m scripts.set_bot_commands
```

## Telegram Commands

```text
/help
Show command guide.

/tasks
Show tasks from Notion.

/tasks progress
Show tasks with status In progress.

/tasks done
Show tasks with status Done.

/tasks review
Show tasks with status Under review.

/tasks todo
Show tasks with status Not started.

/tasks_progress
Shortcut for In progress tasks.

/add Nama task
Create simple task in Notion.
```

## Current MVP Status

Completed:

```text
- Telegram bot webhook
- FastAPI backend
- Notion API integration
- Notion schema mapper
- MCP Notion Server
- MCP Inspector testing
- MCP Client integration for /tasks
```

Next:

```text
- Migrate /add to MCP Client
- Add /receivables command
- Add weekly report
- Add priority scoring
- Add LangGraph natural language agent
```
