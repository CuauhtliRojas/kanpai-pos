import json
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.constants import (
    ActiveStatus,
    PaymentMethodValue,
    TicketLineStatus,
    TicketPaymentStatus,
    TicketStatus,
    audit_event,
)
from app.models import AuditEvent, Payment, PaymentMethod, Ticket, TicketLine
from app.models import TicketDiscount
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.print_service import create_ticket_print_job
from app.services.sales_inventory_service import consume_inventory_for_paid_ticket
from app.services.table_service import release_table_for_paid_ticket
from app.services.ticket_service import get_active_employee, get_ticket

CANCELLED_LINE_STATUSES = (TicketLineStatus.CANCELLED,)


def _normalized_method_text(payment_method: PaymentMethod) -> str:
    return f"{payment_method.method_key} {payment_method.name}".casefold()


def _requires_payment_reference(payment_method: PaymentMethod) -> bool:
    """Apply the operational policy while legacy catalog data is corrected."""
    method_text = _normalized_method_text(payment_method)
    if "transfer" in method_text:
        return True
    if "tarjeta" in method_text or "card" in method_text:
        return False
    return payment_method.requires_reference


def _has_captured_lines(db: Session, ticket_id: int) -> bool:
    return bool(
        db.scalar(
            select(func.count(TicketLine.id)).where(
                TicketLine.ticket_id == ticket_id,
                TicketLine.status == TicketLineStatus.CAPTURED,
            )
        )
    )


def _active_payment_total(db: Session, ticket_id: int) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
                Payment.ticket_id == ticket_id,
                Payment.status == ActiveStatus.ACTIVE,
            )
        )
        or 0
    )


def _has_full_courtesy_discount(db: Session, ticket: Ticket) -> bool:
    """Indica si el total cero proviene de una cortesía autorizada."""
    if ticket.subtotal_cents <= 0 or ticket.total_cents != 0:
        return False

    courtesy_total = int(
        db.scalar(
            select(func.coalesce(func.sum(TicketDiscount.amount_cents), 0)).where(
                TicketDiscount.ticket_id == ticket.id,
                TicketDiscount.is_courtesy.is_(True),
            )
        )
        or 0
    )
    return courtesy_total >= ticket.subtotal_cents and ticket.discount_cents >= ticket.subtotal_cents


def _close_zero_total_courtesy_ticket(
    db: Session, ticket: Ticket, employee_id: int
) -> Ticket:
    """Cierra un ticket totalmente condonado sin crear pago monetario."""
    now = datetime.utcnow()
    previous_status = ticket.status
    previous_payment_status = ticket.payment_status

    ticket.status = TicketStatus.PAID
    ticket.payment_status = TicketPaymentStatus.PAID
    ticket.billing_started_at = ticket.billing_started_at or now
    ticket.paid_at = now
    ticket.closed_by_employee_id = employee_id

    consume_inventory_for_paid_ticket(db, ticket.id, employee_id)
    release_table_for_paid_ticket(db, ticket, employee_id)

    db.add(
        AuditEvent(
            event_type=audit_event("TICKET_PAID"),
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps(
                {
                    "status": previous_status,
                    "payment_status": previous_payment_status,
                    "total_cents": ticket.total_cents,
                }
            ),
            after_snapshot=json.dumps(
                {
                    "status": TicketStatus.PAID,
                    "payment_status": TicketPaymentStatus.PAID,
                    "total_paid_cents": 0,
                    "closed_by": "courtesy",
                }
            ),
        )
    )
    create_ticket_print_job(db, ticket, [])
    db.flush()
    return ticket


def start_payment(db: Session, ticket_id: int, employee_id: int) -> Ticket:
    """Inicia el cobro de un ticket listo sin confirmar la transacción.

    Valida empleado, estado, líneas y total; actualiza ticket y mesa, registra
    auditoría y hace ``flush``. El llamador conserva la responsabilidad del
    ``commit`` o ``rollback``.
    """
    ticket = get_ticket(db, ticket_id)
    get_active_employee(db, employee_id)
    if ticket.status != TicketStatus.OPEN:
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
    if _has_captured_lines(db, ticket_id):
        raise InvalidBusinessDataError("El ticket tiene líneas capturadas pendientes.")
    if ticket.total_cents <= 0:
        if _has_full_courtesy_discount(db, ticket):
            return _close_zero_total_courtesy_ticket(db, ticket, employee_id)
        raise InvalidBusinessDataError("El ticket debe tener un total mayor a cero.")

    ticket.status = TicketStatus.IN_PAYMENT
    ticket.billing_started_at = datetime.utcnow()
    ticket.table.status_cache = TicketStatus.IN_PAYMENT
    db.add(
        AuditEvent(
            event_type=audit_event("PAYMENT_STARTED"),
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps({"status": TicketStatus.OPEN}),
            after_snapshot=json.dumps({"status": TicketStatus.IN_PAYMENT}),
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
    ticket_split_id: int | None = None,
) -> Payment:
    """Registra un pago y cierra el ticket si cubre el total, sin hacer commit.

    El pago, la liberación de mesa, auditoría y trabajo de impresión participan
    en una sola transacción administrada por el llamador.
    """
    ticket = get_ticket(db, ticket_id)
    get_active_employee(db, employee_id)
    if ticket.status != TicketStatus.IN_PAYMENT:
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
    if _requires_payment_reference(payment_method) and not normalized_reference:
        raise InvalidBusinessDataError("El método de pago requiere referencia.")
    is_cash = payment_method.method_key == PaymentMethodValue.CASH
    if is_cash and received_cents is not None and received_cents < amount_cents:
        raise InvalidBusinessDataError(
            "El efectivo recibido no puede ser menor que el monto."
        )

    payment = Payment(
        folio=generate_folio(db, "PAGO"),
        ticket_id=ticket.id,
        ticket_split_id=ticket_split_id,
        cash_shift_id=ticket.cash_shift_id,
        payment_method_id=payment_method.id,
        cashier_employee_id=employee_id,
        amount_cents=amount_cents,
        received_cents=received_cents,
        change_cents=(received_cents - amount_cents)
        if is_cash and received_cents is not None
        else 0,
        reference=normalized_reference,
        status=ActiveStatus.ACTIVE,
    )
    db.add(payment)
    db.flush()

    total_paid = _active_payment_total(db, ticket.id)
    if total_paid < ticket.total_cents:
        db.add(
            AuditEvent(
                event_type=audit_event("PAYMENT_REGISTERED"),
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
    ticket.status = TicketStatus.PAID
    ticket.payment_status = TicketPaymentStatus.PAID
    ticket.paid_at = now
    ticket.closed_by_employee_id = employee_id
    consume_inventory_for_paid_ticket(db, ticket.id, employee_id)
    release_table_for_paid_ticket(db, ticket, employee_id)
    db.add(
        AuditEvent(
            event_type=audit_event("TICKET_PAID"),
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            before_snapshot=json.dumps({"status": TicketStatus.IN_PAYMENT}),
            after_snapshot=json.dumps(
                {"status": TicketStatus.PAID, "total_paid_cents": total_paid}
            ),
        )
    )
    active_payments = list(
        db.execute(
            select(Payment)
            .options(selectinload(Payment.payment_method))
            .where(
                Payment.ticket_id == ticket.id, Payment.status == ActiveStatus.ACTIVE
            )
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
