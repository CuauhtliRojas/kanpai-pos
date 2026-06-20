from fastapi import APIRouter

from app.api.v1.routes import catalog, inventory, operations, pos, printing, system

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(system.router)
api_router.include_router(catalog.router)
api_router.include_router(operations.router)
api_router.include_router(pos.router)
api_router.include_router(inventory.router)
api_router.include_router(printing.router)
