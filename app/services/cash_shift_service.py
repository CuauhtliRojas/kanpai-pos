import json
from datetime import datetime
from app.core.time import local_now_naive

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.constants import (
    ActiveStatus,
    CashShiftStatus,
    PaymentMethodValue,
    PrintStatus,
    TicketStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    CashExpense,
    CashShift,
    DiningTable,
    Employee,
    Payment,
    PaymentMethod,
    PrintJob,
    Ticket,
)
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
from app.services.print_service import create_cash_shift_print_job


def get_current_cash_shift(db: Session) -> CashShift | None:
    """Devuelve el único corte abierto actual, o ``None`` si no existe."""
    return (
        db.execute(
            select(CashShift)
            .where(CashShift.status == CashShiftStatus.OPEN)
            .order_by(CashShift.id)
        )
        .scalars()
        .first()
    )


def open_cash_shift(
    db: Session, employee_id: int, opening_cash_cents: int
) -> CashShift:
    """Abre un corte de caja y registra su auditoría sin hacer ``commit``."""
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError("El empleado no existe.")
    if not employee.active:
        raise BusinessConflictError("El empleado está inactivo.")
    require_employee_permission(db, employee_id, "CASH_SHIFT_OPEN")
    if opening_cash_cents < 0:
        raise InvalidBusinessDataError("El efectivo inicial no puede ser negativo.")
    if get_current_cash_shift(db) is not None:
        raise BusinessConflictError("Ya existe un corte de caja abierto.")

    cash_shift = CashShift(
        folio=generate_folio(db, "CORTE"),
        status=CashShiftStatus.OPEN,
        opened_by_employee_id=employee_id,
        opening_cash_cents=opening_cash_cents,
    )
    db.add(cash_shift)
    db.flush()
    db.add(
        AuditEvent(
            event_type=audit_event("CASH_SHIFT_OPENED"),
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


def _sum_cents(db: Session, statement) -> int:
    """Convierte una suma SQL nullable a centavos enteros."""
    return int(db.scalar(statement) or 0)


def get_cash_shift_summary(db: Session, cash_shift_id: int) -> dict:
    """Calcula el resumen vigente de un corte desde sus tablas operativas.

    Ventas consideran tickets pagados; pagos y gastos solo registros activos.
    Los trabajos pendientes se cuentan exactamente por ``cash_shift_id``.
    """
    cash_shift = db.get(CashShift, cash_shift_id)
    if cash_shift is None:
        raise EntityNotFoundError("El corte de caja no existe.")

    total_sales = _sum_cents(
        db,
        select(func.sum(Ticket.total_cents)).where(
            Ticket.cash_shift_id == cash_shift_id,
            Ticket.status == TicketStatus.PAID,
        ),
    )
    total_paid = _sum_cents(
        db,
        select(func.sum(Payment.amount_cents)).where(
            Payment.cash_shift_id == cash_shift_id,
            Payment.status == ActiveStatus.ACTIVE,
        ),
    )

    def payment_total(method_key: str) -> int:
        return _sum_cents(
            db,
            select(func.sum(Payment.amount_cents))
            .join(PaymentMethod, PaymentMethod.id == Payment.payment_method_id)
            .where(
                Payment.cash_shift_id == cash_shift_id,
                Payment.status == ActiveStatus.ACTIVE,
                PaymentMethod.method_key == method_key,
            ),
        )

    total_expenses = _sum_cents(
        db,
        select(func.sum(CashExpense.amount_cents)).where(
            CashExpense.cash_shift_id == cash_shift_id,
            CashExpense.status == ActiveStatus.ACTIVE,
        ),
    )
    total_cash = payment_total(PaymentMethodValue.CASH)
    status_counts = dict(
        db.execute(
            select(Ticket.status, func.count(Ticket.id))
            .where(Ticket.cash_shift_id == cash_shift_id)
            .group_by(Ticket.status)
        ).all()
    )
    ticket_count = sum(status_counts.values())
    active_expense_count = int(
        db.scalar(
            select(func.count(CashExpense.id)).where(
                CashExpense.cash_shift_id == cash_shift_id,
                CashExpense.status == ActiveStatus.ACTIVE,
            )
        )
        or 0
    )
    pending_print_jobs_count = int(
        db.scalar(
            select(func.count(PrintJob.id)).where(
                PrintJob.cash_shift_id == cash_shift_id,
                PrintJob.status == PrintStatus.PENDING,
            )
        )
        or 0
    )
    expected_cash = cash_shift.opening_cash_cents + total_cash - total_expenses
    return {
        "cash_shift_id": cash_shift.id,
        "folio": cash_shift.folio,
        "status": cash_shift.status,
        "opened_at": cash_shift.opened_at,
        "opening_cash_cents": cash_shift.opening_cash_cents,
        "total_sales_cents": total_sales,
        "total_paid_cents": total_paid,
        "total_cash_cents": total_cash,
        "total_card_cents": payment_total(PaymentMethodValue.CARD),
        "total_transfer_cents": payment_total(PaymentMethodValue.TRANSFER),
        "total_expenses_cents": total_expenses,
        "expected_cash_cents": expected_cash,
        "ticket_count": ticket_count,
        "paid_ticket_count": status_counts.get(TicketStatus.PAID, 0),
        "cancelled_ticket_count": status_counts.get(TicketStatus.CANCELLED, 0),
        "active_expense_count": active_expense_count,
        "pending_print_jobs_count": pending_print_jobs_count,
    }


def close_cash_shift(
    db: Session,
    cash_shift_id: int,
    employee_id: int,
    declared_cash_cents: int,
    note: str | None = None,
    allow_pending_print_jobs: bool = True,
) -> CashShift:
    """Cierra un corte validado y encola su impresión sin hacer ``commit``.

    Rechaza tickets abiertos o en cobro. Los trabajos pendientes solo bloquean
    cuando el llamador desactiva explícitamente ``allow_pending_print_jobs``.
    """
    cash_shift = db.get(CashShift, cash_shift_id)
    if cash_shift is None:
        raise EntityNotFoundError("El corte de caja no existe.")
    if cash_shift.status != CashShiftStatus.OPEN:
        raise BusinessConflictError("El corte de caja no está abierto.")

    get_active_employee(db, employee_id)
    require_employee_permission(db, employee_id, "CASH_SHIFT_CLOSE")
    if declared_cash_cents < 0:
        raise InvalidBusinessDataError("El efectivo declarado no puede ser negativo.")

    blocking_tickets = db.execute(
        select(Ticket, DiningTable)
        .join(DiningTable, DiningTable.id == Ticket.table_id)
        .where(
            Ticket.cash_shift_id == cash_shift_id,
            Ticket.status.in_((TicketStatus.OPEN, TicketStatus.IN_PAYMENT)),
        )
        .order_by(DiningTable.sort_order, Ticket.id)
    ).all()
    if blocking_tickets:
        details = "; ".join(
            f"{table.display_name} ({ticket.folio}, {ticket.status})"
            for ticket, table in blocking_tickets
        )
        raise BusinessConflictError(
            "No puedes cerrar caja porque hay cuentas pendientes: "
            f"{details}. Termina o cobra esas cuentas antes de cerrar. "
            "Si una cuenta no corresponde, pide ayuda al encargado."
        )

    summary = get_cash_shift_summary(db, cash_shift_id)
    if not allow_pending_print_jobs and summary["pending_print_jobs_count"]:
        raise BusinessConflictError("El corte tiene impresiones pendientes.")

    expected_cash = summary["expected_cash_cents"]
    cash_shift.status = CashShiftStatus.CLOSED
    cash_shift.closed_by_employee_id = employee_id
    cash_shift.closed_at = local_now_naive()
    cash_shift.declared_cash_cents = declared_cash_cents
    cash_shift.expected_cash_cents = expected_cash
    cash_shift.cash_difference_cents = declared_cash_cents - expected_cash
    cash_shift.closing_note = note.strip() if note and note.strip() else None
    db.flush()
    create_cash_shift_print_job(db, cash_shift, summary)
    db.add(
        AuditEvent(
            event_type=audit_event("CASH_SHIFT_CLOSED"),
            entity_type="CashShift",
            entity_id=cash_shift.id,
            actor_employee_id=employee_id,
            cash_shift_id=cash_shift.id,
            before_snapshot=json.dumps({"status": CashShiftStatus.OPEN}),
            after_snapshot=json.dumps(
                {
                    "status": CashShiftStatus.CLOSED,
                    "declared_cash_cents": declared_cash_cents,
                    "expected_cash_cents": expected_cash,
                    "cash_difference_cents": cash_shift.cash_difference_cents,
                }
            ),
            reason=cash_shift.closing_note,
        )
    )
    db.flush()
    return cash_shift
