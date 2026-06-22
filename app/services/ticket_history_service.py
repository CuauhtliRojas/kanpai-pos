from datetime import date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.domain.constants import PrintJobType, TicketStatus
from app.models import (
    AuditEvent,
    CashShift,
    DiningTable,
    Payment,
    PaymentMethod,
    PrintJob,
    StationOrder,
    Ticket,
    TicketLine,
    TicketSplit,
)
from app.services.cash_shift_service import get_current_cash_shift
from app.services.exceptions import EntityNotFoundError, InvalidBusinessDataError


def _parse_date_range(
    date_from: str | None, date_to: str | None
) -> tuple[datetime | None, datetime | None]:
    def parse(value: str, field: str, end: bool = False) -> datetime:
        try:
            parsed = date.fromisoformat(value)
        except ValueError as error:
            raise InvalidBusinessDataError(
                f"{field} debe ser una fecha ISO valida (AAAA-MM-DD)."
            ) from error
        result = datetime.combine(parsed, time.min)
        return result + timedelta(days=1) if end else result

    start = parse(date_from, "date_from") if date_from else None
    end = parse(date_to, "date_to", end=True) if date_to else None
    if start is not None and end is not None and start >= end:
        raise InvalidBusinessDataError("date_from no puede ser posterior a date_to.")
    return start, end


def list_ticket_history(
    db: Session,
    cash_shift_id: int | None = None,
    table_id: int | None = None,
    q: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista tickets operativos con agregados pequenos y sin snapshots/auditoria."""
    start, end = _parse_date_range(date_from, date_to)
    if status is not None and status not in {
        TicketStatus.OPEN,
        TicketStatus.IN_PAYMENT,
        TicketStatus.PAID,
        TicketStatus.CANCELLED,
    }:
        raise InvalidBusinessDataError("El estado de ticket no es valido.")

    if cash_shift_id is None:
        current_shift = get_current_cash_shift(db)
        if current_shift is not None:
            cash_shift_id = current_shift.id
        elif start is None and end is None:
            return {"total": 0, "limit": limit, "offset": offset, "items": []}
    elif db.get(CashShift, cash_shift_id) is None:
        raise EntityNotFoundError("El corte de caja no existe.")

    line_counts = (
        select(TicketLine.ticket_id, func.count(TicketLine.id).label("line_count"))
        .group_by(TicketLine.ticket_id)
        .subquery()
    )
    payment_stats = (
        select(
            Payment.ticket_id,
            func.count(Payment.id).label("payment_count"),
            func.group_concat(func.distinct(PaymentMethod.name)).label(
                "payment_method_summary"
            ),
        )
        .join(PaymentMethod, PaymentMethod.id == Payment.payment_method_id)
        .group_by(Payment.ticket_id)
        .subquery()
    )
    print_stats = (
        select(
            PrintJob.ticket_id,
            func.count(PrintJob.id).label("print_job_count"),
            func.max(PrintJob.id).label("latest_print_job_id"),
            func.max(PrintJob.id)
            .filter(PrintJob.job_type == PrintJobType.TICKET)
            .label("latest_ticket_print_job_id"),
        )
        .where(PrintJob.ticket_id.is_not(None))
        .group_by(PrintJob.ticket_id)
        .subquery()
    )
    query = (
        select(
            Ticket.id,
            Ticket.folio,
            Ticket.table_id,
            DiningTable.display_name.label("table_name"),
            Ticket.cash_shift_id,
            Ticket.status,
            Ticket.payment_status,
            Ticket.opened_at,
            Ticket.paid_at,
            Ticket.cancelled_at,
            Ticket.subtotal_cents,
            Ticket.discount_cents,
            Ticket.tax_cents,
            Ticket.total_cents,
            func.coalesce(line_counts.c.line_count, 0).label("line_count"),
            func.coalesce(payment_stats.c.payment_count, 0).label("payment_count"),
            func.coalesce(print_stats.c.print_job_count, 0).label("print_job_count"),
            payment_stats.c.payment_method_summary,
            print_stats.c.latest_print_job_id,
            print_stats.c.latest_ticket_print_job_id,
        )
        .join(DiningTable, DiningTable.id == Ticket.table_id)
        .outerjoin(line_counts, line_counts.c.ticket_id == Ticket.id)
        .outerjoin(payment_stats, payment_stats.c.ticket_id == Ticket.id)
        .outerjoin(print_stats, print_stats.c.ticket_id == Ticket.id)
    )
    filters = []
    if cash_shift_id is not None:
        filters.append(Ticket.cash_shift_id == cash_shift_id)
    if table_id is not None:
        filters.append(Ticket.table_id == table_id)
    if status is not None:
        filters.append(Ticket.status == status)
    if start is not None:
        filters.append(Ticket.opened_at >= start)
    if end is not None:
        filters.append(Ticket.opened_at < end)
    normalized_q = q.strip() if q else ""
    if normalized_q:
        pattern = f"%{normalized_q}%"
        filters.append(
            or_(
                Ticket.folio.ilike(pattern),
                DiningTable.display_name.ilike(pattern),
                DiningTable.table_code.ilike(pattern),
                Ticket.payments.any(
                    or_(Payment.folio.ilike(pattern), Payment.reference.ilike(pattern))
                ),
                select(PrintJob.id)
                .where(PrintJob.ticket_id == Ticket.id, PrintJob.folio.ilike(pattern))
                .exists(),
            )
        )
    query = query.where(*filters)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(
        query.order_by(Ticket.opened_at.desc(), Ticket.id.desc())
        .limit(limit)
        .offset(offset)
    ).mappings()
    items = []
    for row in rows:
        item = dict(row)
        item["can_reprint_ticket"] = item["latest_ticket_print_job_id"] is not None
        items.append(item)
    return {"total": total, "limit": limit, "offset": offset, "items": items}


def get_readonly_ticket(db: Session, ticket_id: int) -> dict:
    """Carga un ticket historico completo sin usar contratos mutables ni auditoria masiva."""
    ticket = db.scalar(
        select(Ticket)
        .options(
            selectinload(Ticket.table),
            selectinload(Ticket.lines).selectinload(TicketLine.variant_selections),
            selectinload(Ticket.lines).selectinload(TicketLine.notes),
            selectinload(Ticket.payments).selectinload(Payment.payment_method),
            selectinload(Ticket.discounts),
            selectinload(Ticket.splits).selectinload(TicketSplit.lines),
        )
        .where(Ticket.id == ticket_id)
    )
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")

    print_job_models = list(
        db.scalars(
            select(PrintJob)
            .where(PrintJob.ticket_id == ticket_id)
            .order_by(PrintJob.created_at.desc(), PrintJob.id.desc())
        )
    )
    print_jobs = [
        {
            "id": job.id,
            "folio": job.folio,
            "job_type": job.job_type,
            "printer_id": job.printer_id,
            "printer_key": job.printer_key_snapshot,
            "ticket_id": job.ticket_id,
            "cash_shift_id": job.cash_shift_id,
            "station_order_id": job.station_order_id,
            "command_batch_id": job.command_batch_id,
            "status": job.status,
            "attempts": job.attempts,
            "claimed_at": job.claimed_at,
            "printed_at": job.printed_at,
            "failed_at": job.failed_at,
            "last_error": job.last_error,
            "next_retry_at": job.next_retry_at,
            "created_at": job.created_at,
        }
        for job in print_job_models
    ]
    station_orders = list(
        db.scalars(
            select(StationOrder)
            .options(selectinload(StationOrder.lines))
            .where(StationOrder.ticket_id == ticket_id)
            .order_by(StationOrder.id)
        )
    )
    audit_event_count = (
        db.scalar(select(func.count(AuditEvent.id)).where(AuditEvent.ticket_id == ticket_id))
        or 0
    )
    payments = [
        {
            "id": payment.id,
            "folio": payment.folio,
            "ticket_split_id": payment.ticket_split_id,
            "payment_method_id": payment.payment_method_id,
            "payment_method_name": payment.payment_method.name,
            "amount_cents": payment.amount_cents,
            "received_cents": payment.received_cents,
            "change_cents": payment.change_cents,
            "reference": payment.reference,
            "status": payment.status,
            "cancelled_at": payment.cancelled_at,
            "created_at": payment.created_at,
        }
        for payment in ticket.payments
    ]
    return {
        "ticket": ticket,
        "table": ticket.table,
        "lines": ticket.lines,
        "discounts": ticket.discounts,
        "payments": payments,
        "splits": ticket.splits,
        "print_jobs": print_jobs,
        "station_orders": station_orders,
        "audit_event_count": audit_event_count,
        "can_reprint_ticket": any(
            job.job_type == PrintJobType.TICKET for job in print_job_models
        ),
        "can_reprint_commands": any(
            job.job_type
            in {
                PrintJobType.COMMAND,
                PrintJobType.COMMAND_CANCELLATION,
                PrintJobType.MODIFICATION,
            }
            for job in print_job_models
        ),
        "is_readonly": True,
    }
