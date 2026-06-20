from sqlalchemy import select
from sqlalchemy.orm import Session
from unicodedata import normalize

from app.models import (
    CashShift,
    Payment,
    PrintJob,
    Printer,
    ProductionStation,
    StationOrder,
    StationOrderLine,
    Ticket,
    TicketLine,
)
from app.services.exceptions import BusinessConflictError, EntityNotFoundError
from app.services.folio_service import generate_folio


def _ascii_text(value: str) -> str:
    """Normaliza texto dinámico al subconjunto ASCII admitido por impresoras."""
    return normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")


def get_active_printer(db: Session, printer_key: str) -> Printer:
    """Resuelve una impresora lógica activa o reporta un conflicto operativo."""
    printer = db.execute(
        select(Printer).where(Printer.printer_key == printer_key)
    ).scalar_one_or_none()
    if printer is None:
        raise EntityNotFoundError(
            f"No existe la impresora con clave {printer_key}."
        )
    if not printer.active:
        raise BusinessConflictError(
            f"La impresora {printer_key} está inactiva."
        )
    return printer


def list_pending_print_jobs(db: Session) -> list[PrintJob]:
    """Lista trabajos pendientes en orden FIFO, sin enviarlos a hardware."""
    return list(
        db.execute(
            select(PrintJob)
            .where(PrintJob.status == "PENDING")
            .order_by(PrintJob.created_at, PrintJob.id)
        ).scalars()
    )


def create_ticket_print_job(
    db: Session, ticket: Ticket, payments: list[Payment]
) -> PrintJob:
    """Encola una impresión lógica, idempotente y ASCII del ticket pagado."""
    printer = get_active_printer(db, "CAJA")
    payment_lines = [
        f"{payment.payment_method.method_key}: {payment.amount_cents / 100:.2f}"
        for payment in payments
    ]
    content = "\n".join(
        [
            "KANPAI",
            "TICKET",
            f"FOLIO: {ticket.folio}",
            f"MESA: {_ascii_text(ticket.table.display_name)}",
            f"TOTAL: {ticket.total_cents / 100:.2f}",
            "PAGOS:",
            *payment_lines,
            "GRACIAS",
        ]
    )
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type="TICKET",
        printer_id=printer.id,
        printer_key_snapshot="CAJA",
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        content_snapshot=content,
        status="PENDING",
        attempts=0,
        idempotency_key=f"TICKET:{ticket.id}",
    )
    db.add(print_job)
    db.flush()
    return print_job


def create_cash_shift_print_job(
    db: Session, cash_shift: CashShift, summary: dict
) -> PrintJob:
    """Encola el corte ASCII en caja con una clave idempotente, sin commit."""
    idempotency_key = f"CORTE:{cash_shift.id}"
    existing = db.execute(
        select(PrintJob).where(PrintJob.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    printer = get_active_printer(db, "CAJA")
    content = "\n".join(
        [
            "KANPAI",
            "CORTE",
            f"FOLIO: {_ascii_text(cash_shift.folio)}",
            f"VENTAS: {summary['total_sales_cents'] / 100:.2f}",
            f"EFECTIVO ESPERADO: {cash_shift.expected_cash_cents / 100:.2f}",
            f"EFECTIVO DECLARADO: {cash_shift.declared_cash_cents / 100:.2f}",
            f"DIFERENCIA: {cash_shift.cash_difference_cents / 100:.2f}",
            f"GASTOS: {summary['total_expenses_cents'] / 100:.2f}",
            f"TICKETS PAGADOS: {summary['paid_ticket_count']}",
            f"TICKETS CANCELADOS: {summary['cancelled_ticket_count']}",
        ]
    )
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type="CORTE",
        printer_id=printer.id,
        printer_key_snapshot="CAJA",
        cash_shift_id=cash_shift.id,
        content_snapshot=content,
        status="PENDING",
        attempts=0,
        idempotency_key=idempotency_key,
    )
    db.add(print_job)
    db.flush()
    return print_job


def create_cancellation_print_job(
    db: Session,
    ticket: Ticket,
    line: TicketLine,
    reason: str | None,
    idempotency_key: str,
) -> PrintJob:
    """Encola una cancelación de comanda ASCII e idempotente para una línea.

    La función resuelve la impresora desde el snapshot de estación y vincula la
    última comanda que contenga la línea cuando esa relación está disponible.
    No confirma la transacción.
    """
    existing = db.execute(
        select(PrintJob).where(PrintJob.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    if line.station_id_snapshot is None:
        raise BusinessConflictError("La línea no tiene estación para cancelar.")
    station = db.get(ProductionStation, line.station_id_snapshot)
    if station is None:
        raise EntityNotFoundError("La estación de la línea no existe.")
    if not station.printer_key:
        raise BusinessConflictError(
            f"La estación {station.name} no tiene impresora configurada."
        )
    printer = get_active_printer(db, station.printer_key)
    station_order_id = db.execute(
        select(StationOrder.id)
        .join(StationOrderLine, StationOrderLine.station_order_id == StationOrder.id)
        .where(StationOrderLine.ticket_line_id == line.id)
        .order_by(StationOrder.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    content = "\n".join(
        [
            "KANPAI",
            "CANCELACION COMANDA",
            f"FOLIO: {_ascii_text(ticket.folio)}",
            f"ESTACION: {_ascii_text(station.name)}",
            f"PRODUCTO: {_ascii_text(line.product_name_snapshot)}",
            f"CANTIDAD: {line.quantity}",
            f"MOTIVO: {_ascii_text(reason or 'SIN MOTIVO')}",
        ]
    )
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type="CANCELACION_COMANDA",
        printer_id=printer.id,
        printer_key_snapshot=printer.printer_key,
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        station_order_id=station_order_id,
        content_snapshot=content,
        status="PENDING",
        attempts=0,
        idempotency_key=idempotency_key,
    )
    db.add(print_job)
    db.flush()
    return print_job
