from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.preflight import PreflightResponse
from app.services.preflight_service import run_local_backend_preflight

router = APIRouter(prefix="/preflight", tags=["preflight"])


@router.get("/local-backend", response_model=PreflightResponse)
def local_backend_preflight_endpoint(
    db: Session = Depends(get_db),
) -> PreflightResponse:
    """Report local schema, seed and operational invariant health."""
    return PreflightResponse.model_validate(run_local_backend_preflight(db))
