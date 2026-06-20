import json

from sqlalchemy.orm import Session

from app.domain.constants import ActiveStatus, audit_event
from app.models import AuditEvent, CashExpense, PaymentMethod
from app.services.cash_shift_service import get_current_cash_shift
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.permission_service import (
    get_active_employee,
    require_employee_permission,
)


def create_cash_expense(
    db: Session,
    employee_id: int,
    amount_cents: int,
    description: str,
    category: str | None = None,
    payment_method_id: int | None = None,
    note: str | None = None,
) -> CashExpense:
    """Registra un gasto en el corte abierto, con permiso y sin hacer commit.

    Valida empleado, permiso, monto, descripción y método de pago opcional;
    genera folio, auditoría y hace ``flush`` dentro de la transacción llamadora.
    """
    cash_shift = get_current_cash_shift(db)
    if cash_shift is None:
        raise BusinessConflictError("No existe un corte de caja abierto.")

    get_active_employee(db, employee_id)
    require_employee_permission(db, employee_id, "EXPENSE_CREATE")
    if amount_cents <= 0:
        raise InvalidBusinessDataError("El monto debe ser mayor a cero.")

    normalized_description = description.strip()
    if not normalized_description:
        raise InvalidBusinessDataError("La descripción no puede estar vacía.")

    if payment_method_id is not None:
        payment_method = db.get(PaymentMethod, payment_method_id)
        if payment_method is None:
            raise EntityNotFoundError("El método de pago no existe.")
        if not payment_method.active:
            raise BusinessConflictError("El método de pago está inactivo.")

    expense = CashExpense(
        folio=generate_folio(db, "GASTO"),
        cash_shift_id=cash_shift.id,
        registered_by_employee_id=employee_id,
        amount_cents=amount_cents,
        description=normalized_description,
        category=category.strip() if category and category.strip() else None,
        payment_method_id=payment_method_id,
        note=note.strip() if note and note.strip() else None,
        status=ActiveStatus.ACTIVE,
    )
    db.add(expense)
    db.flush()
    db.add(
        AuditEvent(
            event_type=audit_event("CASH_EXPENSE_CREATED"),
            entity_type="CashExpense",
            entity_id=expense.id,
            actor_employee_id=employee_id,
            cash_shift_id=cash_shift.id,
            after_snapshot=json.dumps(
                {
                    "folio": expense.folio,
                    "amount_cents": expense.amount_cents,
                    "description": expense.description,
                    "category": expense.category,
                    "payment_method_id": expense.payment_method_id,
                    "status": expense.status,
                },
                ensure_ascii=False,
            ),
        )
    )
    db.flush()
    return expense
