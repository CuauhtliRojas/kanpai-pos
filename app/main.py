import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.airtable_sync_scheduler import get_airtable_sync_scheduler

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = get_airtable_sync_scheduler()
    try:
        await scheduler.start()
    except Exception:
        logger.exception("Airtable scheduler could not start; API startup will continue.")
    try:
        yield
    finally:
        await scheduler.stop()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "database": "sqlite",
    }
