from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.security import require_support_permission
from app.schemas.preflight import PreflightResponse
from app.services.preflight_service import run_local_backend_preflight

router = APIRouter(prefix="/preflight", tags=["preflight"])


@router.get(
    "/local-backend",
    response_model=PreflightResponse,
    dependencies=[Depends(require_support_permission)],
    tags=["preflight", "admin-support"],
    summary="Ejecutar preflight local (admin/soporte)",
    description="Diagnóstico operativo read-only protegido por sesión administrativa o de soporte.",
)
def local_backend_preflight_endpoint(
    db: Session = Depends(get_db),
) -> PreflightResponse:
    """Report local schema, seed and operational invariant health."""
    return PreflightResponse.model_validate(run_local_backend_preflight(db))
