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
    
    GROQ_API_KEY : str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    WEEKLY_REPORT_DAY_OF_WEEK: str = os.getenv("WEEKLY_REPORT_DAY_OF_WEEK", "sun")
    WEEKLY_REPORT_HOUR: int = int(os.getenv("WEEKLY_REPORT_HOUR", "7"))
    WEEKLY_REPORT_MINUTE: int = int(os.getenv("WEEKLY_REPORT_MINUTE", "0"))
    WEEKLY_REPORT_TIMEZONE: str = os.getenv("WEEKLY_REPORT_TIMEZONE", "Asia/Jakarta")
    
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