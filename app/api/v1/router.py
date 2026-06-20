from fastapi import APIRouter

from app.api.v1.routes import catalog, operations, pos, system

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(system.router)
api_router.include_router(catalog.router)
api_router.include_router(operations.router)
api_router.include_router(pos.router)
