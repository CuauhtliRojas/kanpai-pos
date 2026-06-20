import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, CashShift, Employee
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio


def get_current_cash_shift(db: Session) -> CashShift | None:
    """Devuelve el único corte abierto actual, o ``None`` si no existe."""
    return db.execute(
        select(CashShift).where(CashShift.status == "OPEN").order_by(CashShift.id)
    ).scalars().first()


def open_cash_shift(
    db: Session, employee_id: int, opening_cash_cents: int
) -> CashShift:
    """Abre un corte de caja y registra su auditoría sin hacer ``commit``."""
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError("El empleado no existe.")
    if not employee.active:
        raise BusinessConflictError("El empleado está inactivo.")
    if opening_cash_cents < 0:
        raise InvalidBusinessDataError(
            "El efectivo inicial no puede ser negativo."
        )
    if get_current_cash_shift(db) is not None:
        raise BusinessConflictError("Ya existe un corte de caja abierto.")

    cash_shift = CashShift(
        folio=generate_folio(db, "CORTE"),
        status="OPEN",
        opened_by_employee_id=employee_id,
        opening_cash_cents=opening_cash_cents,
    )
    db.add(cash_shift)
    db.flush()
    db.add(
        AuditEvent(
            event_type="CASH_SHIFT_OPENED",
            entity_type="CashShift",
            entity_id=cash_shift.id,
            actor_employee_id=employee_id,
            cash_shift_id=cash_shift.id,
            after_snapshot=json.dumps(
                {
                    "folio": cash_shift.folio,
                    "status": cash_shift.status,
                    "opening_cash_cents": opening_cash_cents,
                }
            ),
        )
    )
    db.flush()
    return cash_shift
