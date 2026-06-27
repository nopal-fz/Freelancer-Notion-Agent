from fastapi import FastAPI

from app.config import settings
from app.logging_config import setup_logging
from app.telegram.webhook import router as telegram_router

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
)

# Health check endpoint to verify the application is running
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }

app.include_router(telegram_router)