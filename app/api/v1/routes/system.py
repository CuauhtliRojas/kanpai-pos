from sqlalchemy import select, text
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.database import get_db
from app.api.security import require_support_permission
from app.models import (
    BusinessSetting,
    DiningTable,
    Employee,
    MenuCategory,
    PaymentMethod,
    ProductionStation,
)
from app.schemas.business_setting import BusinessSettingResponse
from app.services.airtable_sync_scheduler import get_airtable_sync_scheduler

router = APIRouter(prefix="/system", tags=["system"])


class AirtableSyncRequest(BaseModel):
    dry_run: bool = True
    confirm: str | None = None
    force_pull_during_active_shift: bool = False


def _airtable_sync_response_or_error(result: dict) -> dict:
    if result.get("accepted", True):
        return result
    code = status.HTTP_400_BAD_REQUEST
    if result.get("status") in {"busy", "missing_credentials"}:
        code = status.HTTP_409_CONFLICT
    raise HTTPException(status_code=code, detail=result)




@router.get("/airtable-sync")
def airtable_sync_status() -> dict:
    return get_airtable_sync_scheduler().status()




@router.post("/airtable-sync/pull")
async def airtable_sync_pull(request: AirtableSyncRequest | None = None) -> dict:
    payload = request or AirtableSyncRequest()
    result = await get_airtable_sync_scheduler().run_manual(
        pull=True,
        push=False,
        dry_run=payload.dry_run,
        confirm=payload.confirm,
        force_pull_during_active_shift=payload.force_pull_during_active_shift,
    )
    return _airtable_sync_response_or_error(result)


@router.post("/airtable-sync/push")
async def airtable_sync_push(request: AirtableSyncRequest | None = None) -> dict:
    payload = request or AirtableSyncRequest()
    result = await get_airtable_sync_scheduler().run_manual(
        pull=False,
        push=True,
        dry_run=payload.dry_run,
        confirm=payload.confirm,
        force_pull_during_active_shift=payload.force_pull_during_active_shift,
    )
    return _airtable_sync_response_or_error(result)


@router.post("/airtable-sync/run")
async def airtable_sync_run(request: AirtableSyncRequest | None = None) -> dict:
    payload = request or AirtableSyncRequest()
    result = await get_airtable_sync_scheduler().run_manual(
        pull=True,
        push=True,
        dry_run=payload.dry_run,
        confirm=payload.confirm,
        force_pull_during_active_shift=payload.force_pull_during_active_shift,
    )
    return _airtable_sync_response_or_error(result)


@router.get("/business-settings", response_model=BusinessSettingResponse)
def business_settings(db: Session = Depends(get_db)) -> BusinessSettingResponse:
    """Expose the active fiscal policy used by all ticket recalculations."""
    setting = db.scalar(select(BusinessSetting).where(BusinessSetting.active.is_(True)))
    if setting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe configuracion de negocio activa.",
        )
    return BusinessSettingResponse.model_validate(setting)


@router.get(
    "/db",
    dependencies=[Depends(require_support_permission)],
    tags=["system", "admin-support"],
    summary="Verificar base local (admin/soporte)",
    description="Diagnóstico local protegido por sesión administrativa o de soporte.",
)
def database_status(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "sqlite",
    }


@router.get(
    "/seed-summary",
    dependencies=[Depends(require_support_permission)],
    tags=["system", "admin-support"],
    summary="Consultar resumen de seed (admin/soporte)",
    description="Conteos de diagnóstico protegidos por sesión administrativa o de soporte.",
)
def seed_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    business_count = len(db.execute(select(BusinessSetting)).scalars().all())
    table_count = len(db.execute(select(DiningTable)).scalars().all())
    category_count = len(db.execute(select(MenuCategory)).scalars().all())
    station_count = len(db.execute(select(ProductionStation)).scalars().all())
    payment_method_count = len(db.execute(select(PaymentMethod)).scalars().all())
    employee_count = len(db.execute(select(Employee)).scalars().all())

    return {
        "business_settings": business_count,
        "tables": table_count,
        "categories": category_count,
        "stations": station_count,
        "payment_methods": payment_method_count,
        "employees": employee_count,
    }
