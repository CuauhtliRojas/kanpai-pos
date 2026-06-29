import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.services.airtable_sync_scheduler import get_airtable_sync_scheduler

settings = get_settings()
logger = logging.getLogger(__name__)


def build_cors_origins() -> list[str]:
    """Origenes permitidos para operar Kanpai POS local y empaquetado."""
    origins = set(settings.cors_origin_list)
    origins.update(
        {
            "tauri://localhost",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "http://localhost:1420",
            "http://127.0.0.1:1420",
        }
    )
    return sorted(origin for origin in origins if origin)


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

settings.resolved_product_image_media_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.product_image_media_url,
    StaticFiles(directory=settings.resolved_product_image_media_dir),
    name="product-images",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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


