import os
from dotenv import load_dotenv

load_dotenv()

# Configuration class to manage application settings
class Settings:
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_NAME: str = os.getenv("APP_NAME", "FreelancerOS AI Agent")

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

    ALLOWED_TELEGRAM_USER_IDS_RAW: str = os.getenv(
        "ALLOWED_TELEGRAM_USER_IDS",
        "",
    )

    NOTION_API_KEY: str = os.getenv("NOTION_API_KEY", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")
    NOTION_API_VERSION: str = os.getenv("NOTION_API_VERSION", "2022-06-28")
    
    MCP_NOTION_SERVER_URL: str = os.getenv(
    "MCP_NOTION_SERVER_URL",
    "http://127.0.0.1:8101/mcp",
    )

    @property
    def allowed_telegram_user_ids(self) -> set[int]:
        if not self.ALLOWED_TELEGRAM_USER_IDS_RAW.strip():
            return set()

        return {
            int(user_id.strip())
            for user_id in self.ALLOWED_TELEGRAM_USER_IDS_RAW.split(",")
            if user_id.strip()
        }

    @property
    def telegram_api_base_url(self) -> str:
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not configured.")

        return f"https://api.telegram.org/bot{self.TELEGRAM_BOT_TOKEN}"


settings = Settings()