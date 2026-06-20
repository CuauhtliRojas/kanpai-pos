from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    BusinessErrorResponse,
    PrintJobClaimRequest,
    PrintJobClaimResponse,
    PrintJobFailedRequest,
    PrintJobResponse,
    PrintJobRetryRequest,
    PrintJobRetryResponse,
    PrintJobWorkerRequest,
)
from app.services.exceptions import (
    BusinessConflictError,
    BusinessError,
    EntityNotFoundError,
    InvalidBusinessDataError,
    PermissionDeniedError,
)
from app.schemas.reprint import ReprintRequest
from app.services.reprint_service import get_print_job, request_reprint
from app.services.print_queue_service import (
    claim_next_print_job,
    list_pending_print_jobs,
    mark_print_job_failed,
    mark_print_job_printed,
    retry_failed_print_jobs,
)

router = APIRouter(prefix="/printing", tags=["printing"])

BUSINESS_ERROR_RESPONSES = {
    400: {"model": BusinessErrorResponse},
    403: {"model": BusinessErrorResponse},
    404: {"model": BusinessErrorResponse},
    409: {"model": BusinessErrorResponse},
}


def _to_http_exception(error: BusinessError) -> HTTPException:
    """Mapea errores esperados de cola sin exponer detalles internos."""
    if isinstance(error, InvalidBusinessDataError):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(error, EntityNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(error, PermissionDeniedError):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(error, BusinessConflictError):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail=str(error))


@router.get(
    "/jobs/pending",
    response_model=list[PrintJobResponse],
    responses=BUSINESS_ERROR_RESPONSES,
)
def list_pending_print_jobs_endpoint(
    printer_key: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[PrintJobResponse]:
    """Expone la cola pendiente en orden FIFO para monitoreo o polling."""
    try:
        return [
            PrintJobResponse.model_validate(job)
            for job in list_pending_print_jobs(db, printer_key, limit)
        ]
    except BusinessError as error:
        raise _to_http_exception(error) from None


@router.post(
    "/jobs/claim-next",
    response_model=PrintJobClaimResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def claim_next_print_job_endpoint(
    payload: PrintJobClaimRequest, db: Session = Depends(get_db)
) -> PrintJobClaimResponse:
    """Entrega al daemon el siguiente trabajo disponible para su impresora."""
    try:
        print_job = claim_next_print_job(db, payload.printer_key, payload.worker_id)
        response = PrintJobClaimResponse(
            job=PrintJobResponse.model_validate(print_job) if print_job else None
        )
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/jobs/{print_job_id}/printed",
    response_model=PrintJobResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def mark_print_job_printed_endpoint(
    print_job_id: int,
    payload: PrintJobWorkerRequest,
    db: Session = Depends(get_db),
) -> PrintJobResponse:
    """Confirma que el daemon terminó la impresión física del snapshot."""
    try:
        print_job = mark_print_job_printed(db, print_job_id, payload.worker_id)
        response = PrintJobResponse.model_validate(print_job)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/jobs/{print_job_id}/failed",
    response_model=PrintJobResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def mark_print_job_failed_endpoint(
    print_job_id: int,
    payload: PrintJobFailedRequest,
    db: Session = Depends(get_db),
) -> PrintJobResponse:
    """Registra el error reportado por el daemon y agenda el retry."""
    try:
        print_job = mark_print_job_failed(
            db, print_job_id, payload.worker_id, payload.error_message
        )
        response = PrintJobResponse.model_validate(print_job)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.post(
    "/jobs/retry-failed",
    response_model=PrintJobRetryResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def retry_failed_print_jobs_endpoint(
    payload: PrintJobRetryRequest, db: Session = Depends(get_db)
) -> PrintJobRetryResponse:
    """Reactiva trabajos fallidos vencidos o seleccionados manualmente."""
    try:
        jobs_requeued = retry_failed_print_jobs(
            db, payload.printer_key, payload.reset_all
        )
        db.commit()
        return PrintJobRetryResponse(jobs_requeued=jobs_requeued)
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None


@router.get(
    "/jobs/{print_job_id}",
    response_model=PrintJobResponse,
    responses=BUSINESS_ERROR_RESPONSES,
)
def get_print_job_endpoint(
    print_job_id: int, db: Session = Depends(get_db)
) -> PrintJobResponse:
    try:
        return PrintJobResponse.model_validate(get_print_job(db, print_job_id))
    except BusinessError as error:
        raise _to_http_exception(error) from None


@router.post(
    "/jobs/{print_job_id}/reprint",
    response_model=PrintJobResponse,
    status_code=status.HTTP_201_CREATED,
    responses=BUSINESS_ERROR_RESPONSES,
)
def reprint_job_endpoint(
    print_job_id: int,
    payload: ReprintRequest,
    db: Session = Depends(get_db),
) -> PrintJobResponse:
    try:
        job = request_reprint(db, print_job_id, payload.employee_id, payload.reason)
        response = PrintJobResponse.model_validate(job)
        db.commit()
        return response
    except BusinessError as error:
        db.rollback()
        raise _to_http_exception(error) from None
