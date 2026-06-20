from fastapi import APIRouter

from app.api.v1.routes import (
    audit,
    auth,
    catalog,
    inventory,
    notifications,
    operations,
    pos,
    preflight,
    production,
    printing,
    reports,
    system,
    splits,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(system.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(operations.router)
api_router.include_router(pos.router)
api_router.include_router(splits.router)
api_router.include_router(inventory.router)
api_router.include_router(notifications.router)
api_router.include_router(printing.router)
api_router.include_router(production.router)
api_router.include_router(reports.router)
api_router.include_router(audit.router)
api_router.include_router(preflight.router)
