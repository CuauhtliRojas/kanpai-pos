import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import AuditEvent, Payment, PaymentMethod, Ticket, TicketLine
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.print_service import create_ticket_print_job
from app.services.table_service import release_table_for_paid_ticket
from app.services.ticket_service import get_active_employee, get_ticket

CANCELLED_LINE_STATUSES = ("CANCELLED", "CANCELED", "CANCELADO")


def _has_captured_lines(db: Session, ticket_id: int) -> bool:
    return bool(
        db.scalar(
            select(func.count(TicketLine.id)).where(
                TicketLine.ticket_id == ticket_id,
                TicketLine.status == "CAPTURED",
            )
        )
    )


def _active_payment_total(db: Session, ticket_id: int) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                Payment.ticket_id == ticket_id,
                Payment.status == "ACTIVE",
            )
        )
        or 0
    )


def start_payment(db: Session, ticket_id: int, employee_id: int) -> Ticket:
    """Inicia el cobro de un ticket listo sin confirmar la transacción.

    Valida empleado, estado, líneas y total; actualiza ticket y mesa, registra
    auditoría y hace ``flush``. El llamador conserva la responsabilidad del
    ``commit`` o ``rollback``.
    """
    ticket = get_ticket(db, ticket_id)
    get_active_employee(db, employee_id)
    if ticket.status != "OPEN":
        raise BusinessConflictError(
            f"El ticket no puede iniciar cobro desde el estado {ticket.status}."
        )

    active_line_count = db.scalar(
        select(func.count(TicketLine.id)).where(
            TicketLine.ticket_id == ticket_id,
            TicketLine.status.not_in(CANCELLED_LINE_STATUSES),
        )
    )
    if not active_line_count:
        raise InvalidBusinessDataError("El ticket no tiene líneas activas.")
    if ticket.total_cents <= 0:
        raise InvalidBusinessDataError("El ticket debe tener un total mayor a cero.")
    if _has_captured_lines(db, ticket_id):
        raise InvalidBusinessDataError("El ticket tiene líneas capturadas pendientes.")

    ticket.status = "IN_PAYMENT"
    ticket.billing_started_at = datetime.utcnow()
    ticket.table.status_cache = "IN_PAYMENT"
    db.add(
        AuditEvent(
            event_type="PAYMENT_STARTED",
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps({"status": "OPEN"}),
            after_snapshot=json.dumps({"status": "IN_PAYMENT"}),
        )
    )
    db.flush()
    return ticket


def create_payment(
    db: Session,
    ticket_id: int,
    employee_id: int,
    payment_method_id: int,
    amount_cents: int,
    received_cents: int | None = None,
    reference: str | None = None,
) -> Payment:
    """Registra un pago y cierra el ticket si cubre el total, sin hacer commit.

    El pago, la liberación de mesa, auditoría y trabajo de impresión participan
    en una sola transacción administrada por el llamador.
    """
    ticket = get_ticket(db, ticket_id)
    get_active_employee(db, employee_id)
    if ticket.status != "IN_PAYMENT":
        raise BusinessConflictError(
            f"El ticket no acepta pagos desde el estado {ticket.status}."
        )

    payment_method = db.get(PaymentMethod, payment_method_id)
    if payment_method is None:
        raise EntityNotFoundError("El método de pago no existe.")
    if not payment_method.active:
        raise BusinessConflictError("El método de pago está inactivo.")
    if amount_cents <= 0:
        raise InvalidBusinessDataError("El monto debe ser mayor a cero.")

    normalized_reference = reference.strip() if reference else None
    if payment_method.requires_reference and not normalized_reference:
        raise InvalidBusinessDataError("El método de pago requiere referencia.")
    is_cash = payment_method.method_key == "CASH"
    if is_cash and received_cents is not None and received_cents < amount_cents:
        raise InvalidBusinessDataError(
            "El efectivo recibido no puede ser menor que el monto."
        )

    payment = Payment(
        folio=generate_folio(db, "PAGO"),
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        payment_method_id=payment_method.id,
        cashier_employee_id=employee_id,
        amount_cents=amount_cents,
        received_cents=received_cents,
        change_cents=(received_cents - amount_cents)
        if is_cash and received_cents is not None
        else 0,
        reference=normalized_reference,
        status="ACTIVE",
    )
    db.add(payment)
    db.flush()

    total_paid = _active_payment_total(db, ticket.id)
    if total_paid < ticket.total_cents:
        db.add(
            AuditEvent(
                event_type="PAYMENT_REGISTERED",
                entity_type="Payment",
                entity_id=payment.id,
                actor_employee_id=employee_id,
                cash_shift_id=ticket.cash_shift_id,
                ticket_id=ticket.id,
                after_snapshot=json.dumps(
                    {"amount_cents": amount_cents, "total_paid_cents": total_paid}
                ),
            )
        )
        db.flush()
        return payment

    if _has_captured_lines(db, ticket.id):
        raise InvalidBusinessDataError("El ticket tiene líneas capturadas pendientes.")

    now = datetime.utcnow()
    ticket.status = "PAID"
    ticket.payment_status = "PAID"
    ticket.paid_at = now
    ticket.closed_by_employee_id = employee_id
    release_table_for_paid_ticket(db, ticket, employee_id)
    db.add(
        AuditEvent(
            event_type="TICKET_PAID",
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps({"status": "IN_PAYMENT"}),
            after_snapshot=json.dumps(
                {"status": "PAID", "total_paid_cents": total_paid}
            ),
        )
    )
    active_payments = list(
        db.execute(
            select(Payment)
            .options(selectinload(Payment.payment_method))
            .where(Payment.ticket_id == ticket.id, Payment.status == "ACTIVE")
            .order_by(Payment.id)
        ).scalars()
    )
    create_ticket_print_job(db, ticket, active_payments)
    db.flush()
    return payment


def list_ticket_payments(db: Session, ticket_id: int) -> list[Payment]:
    """Lista todos los pagos del ticket, incluidos activos y cancelados."""
    get_ticket(db, ticket_id)
    return list(
        db.execute(
            select(Payment)
            .where(Payment.ticket_id == ticket_id)
            .order_by(Payment.created_at, Payment.id)
        ).scalars()
    )


def get_active_payment_total(db: Session, ticket_id: int) -> int:
    """Devuelve la suma vigente de pagos activos de un ticket existente."""
    get_ticket(db, ticket_id)
    return _active_payment_total(db, ticket_id)
