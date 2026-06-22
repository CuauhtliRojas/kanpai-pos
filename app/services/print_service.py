import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from unicodedata import normalize

from app.core.config import get_settings
from app.domain.constants import PrintJobType, PrintStatus, TicketLineStatus
from app.models import (
    CashShift,
    Employee,
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
from app.services.print_formatters import (
    format_cancellation_80mm,
    format_cash_shift_58mm,
    format_command_80mm,
    format_modification_80mm,
    format_ticket_58mm,
)
from app.services.print_profile import get_print_profile


def sanitize_print_content(content: str, *, ascii_only: bool = True) -> str:
    """Normaliza contenido imprimible y conserva saltos de linea.

    Por defecto produce ASCII seguro para comandas/worker ESC/POS legacy.
    Para ticket cliente se permite Unicode para conservar el mensaje japones.
    """

    def repair_mojibake(match: re.Match[str]) -> str:
        try:
            return match.group(0).encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return match.group(0)

    content = re.sub(r"\S*[\u00c3\u00c2\u00e2]\S*", repair_mojibake, content)
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    if ascii_only:
        content = normalize("NFKD", content).encode("ascii", "ignore").decode("ascii")
    else:
        content = normalize("NFKC", content)

    return "".join(
        character
        for character in content
        if character == "\n" or ord(character) >= 32
    )


def _first_text(*values: Any) -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _employee_name(employee: Employee | None) -> str:
    if employee is None:
        return ""
    return _first_text(
        getattr(employee, "pos_alias", None),
        getattr(employee, "full_name", None),
        getattr(employee, "employee_code", None),
    )


def _ticket_datetime(ticket: Ticket) -> Any:
    return (
        getattr(ticket, "paid_at", None)
        or getattr(ticket, "payment_date", None)
        or getattr(ticket, "updated_at", None)
        or getattr(ticket, "created_at", None)
        or getattr(ticket, "opened_at", None)
    )


def _line_variants(line: TicketLine) -> list[str]:
    variants: list[str] = []
    for selection in getattr(line, "variant_selections", []) or []:
        name = _first_text(getattr(selection, "name_snapshot", None))
        if not name:
            continue
        quantity = int(getattr(selection, "quantity", 1) or 1)
        variants.append(f"{quantity} x {name}" if quantity > 1 else name)
    return variants


def _line_payload(line: TicketLine, *, include_total: bool) -> dict:
    payload = {
        "quantity": getattr(line, "quantity", 1),
        "name": getattr(line, "product_name_snapshot", "") or "Producto",
        "variants": _line_variants(line),
        "note": getattr(line, "note", None),
    }
    if include_total:
        payload["total_cents"] = getattr(line, "line_total_cents", 0)
    return payload


def _ticket_items(db: Session, ticket: Ticket) -> list[dict]:
    lines = list(
        db.execute(
            select(TicketLine)
            .where(TicketLine.ticket_id == ticket.id)
            .order_by(TicketLine.id)
        ).scalars()
    )
    items = []
    for line in lines:
        if getattr(line, "status", None) == TicketLineStatus.CANCELLED:
            continue
        if getattr(line, "parent_ticket_line_id", None) is not None:
            continue
        items.append(_line_payload(line, include_total=True))
    return items


def _payment_payload(payment: Payment) -> dict:
    method = getattr(payment, "payment_method", None)
    return {
        "method": _first_text(
            getattr(method, "method_key", None),
            getattr(method, "name", None),
            "Pago",
        ),
        "amount_cents": getattr(payment, "amount_cents", 0),
    }


def build_command_content(
    ticket: Ticket,
    station: ProductionStation,
    round_number: int,
    lines: list[TicketLine],
) -> str:
    profile = get_print_profile()
    content = format_command_80mm(
        {
            "title": profile.command_title,
            "folio": ticket.folio,
            "table": ticket.table.display_name,
            "created_at": datetime.utcnow(),
            "station": station.name,
            "round": round_number,
            "items": [_line_payload(line, include_total=False) for line in lines],
        }
    )
    return sanitize_print_content(content)


def build_cancellation_content(
    ticket: Ticket,
    station: ProductionStation,
    line: TicketLine,
    reason: str | None,
) -> str:
    profile = get_print_profile()
    content = format_cancellation_80mm(
        {
            "title": profile.cancel_title,
            "folio": ticket.folio,
            "table": ticket.table.display_name,
            "created_at": datetime.utcnow(),
            "station": station.name,
            "round": getattr(line, "round_number", None),
            "items": [_line_payload(line, include_total=False)],
            "reason": reason or "Sin motivo",
        }
    )
    return sanitize_print_content(content)


def build_modification_content(
    ticket: Ticket,
    station: ProductionStation,
    line: TicketLine,
    note_text: str,
) -> str:
    profile = get_print_profile()
    content = format_modification_80mm(
        {
            "title": profile.modification_title,
            "folio": ticket.folio,
            "table": ticket.table.display_name,
            "created_at": datetime.utcnow(),
            "station": station.name,
            "before_items": [_line_payload(line, include_total=False)],
            "after_items": [
                {
                    **_line_payload(line, include_total=False),
                    "note": note_text,
                }
            ],
            "reason": note_text,
        }
    )
    return sanitize_print_content(content)


def get_active_printer(
    db: Session,
    printer_key: str,
    *,
    allow_inactive_in_development: bool = False,
) -> Printer:
    """Resuelve una impresora logica activa o reporta un conflicto operativo."""
    printer = db.execute(
        select(Printer).where(Printer.printer_key == printer_key)
    ).scalar_one_or_none()
    if printer is None:
        raise EntityNotFoundError(f"No existe la impresora con clave {printer_key}.")
    if not printer.active:
        settings = get_settings()
        is_development = settings.app_env.strip().lower() in {
            "local",
            "development",
            "dev",
        }
        bypass_enabled = (
            allow_inactive_in_development
            and is_development
            and settings.pos_dev_bypass_printer_active_check
        )
        if not bypass_enabled:
            raise BusinessConflictError(f"La impresora {printer_key} esta inactiva.")
    return printer


def list_pending_print_jobs(db: Session) -> list[PrintJob]:
    """Lista trabajos pendientes en orden FIFO, sin enviarlos a hardware."""
    return list(
        db.execute(
            select(PrintJob)
            .where(PrintJob.status == PrintStatus.PENDING)
            .order_by(PrintJob.created_at, PrintJob.id)
        ).scalars()
    )


def create_ticket_print_job(
    db: Session, ticket: Ticket, payments: list[Payment]
) -> PrintJob:
    """Encola una impresion logica e idempotente del ticket pagado."""
    profile = get_print_profile()
    printer = get_active_printer(db, "CAJA")
    cashier = db.get(Employee, ticket.closed_by_employee_id)
    content = format_ticket_58mm(
        {
            "business_name": profile.brand_name,
            "brand_name": profile.brand_name,
            "folio": ticket.folio,
            "table": ticket.table.display_name,
            "created_at": _ticket_datetime(ticket),
            "cashier": _employee_name(cashier),
            "items": _ticket_items(db, ticket),
            "subtotal_cents": ticket.subtotal_cents,
            "discount_cents": ticket.discount_cents,
            "total_cents": ticket.total_cents,
            "payments": [_payment_payload(payment) for payment in payments],
            "ticket_message": profile.ticket_message,
        }
    )
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type=PrintJobType.TICKET,
        printer_id=printer.id,
        printer_key_snapshot="CAJA",
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        content_snapshot=sanitize_print_content(content, ascii_only=False),
        status=PrintStatus.PENDING,
        attempts=0,
        idempotency_key=f"TICKET:{ticket.id}",
    )
    db.add(print_job)
    db.flush()
    return print_job


def create_cash_shift_print_job(
    db: Session, cash_shift: CashShift, summary: dict
) -> PrintJob:
    """Encola el corte en caja con una clave idempotente, sin commit."""
    idempotency_key = f"CORTE:{cash_shift.id}"
    existing = db.execute(
        select(PrintJob).where(PrintJob.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    profile = get_print_profile()
    printer = get_active_printer(db, "CAJA")
    cashier = db.get(Employee, cash_shift.closed_by_employee_id)
    content = format_cash_shift_58mm(
        {
            "business_name": profile.brand_name,
            "brand_name": profile.brand_name,
            "folio": cash_shift.folio,
            "opened_at": cash_shift.opened_at,
            "closed_at": cash_shift.closed_at,
            "cashier": _employee_name(cashier),
            "net_sales_cents": summary["total_sales_cents"],
            "payments_by_method": [
                {"method": "Efectivo", "amount_cents": summary.get("total_cash_cents", 0)},
                {"method": "Tarjeta", "amount_cents": summary.get("total_card_cents", 0)},
                {
                    "method": "Transferencia",
                    "amount_cents": summary.get("total_transfer_cents", 0),
                },
            ],
            "opening_cash_cents": summary.get("opening_cash_cents", 0),
            "expected_cash_cents": cash_shift.expected_cash_cents,
            "declared_cash_cents": cash_shift.declared_cash_cents,
            "cash_difference_cents": cash_shift.cash_difference_cents,
            "paid_ticket_count": summary["paid_ticket_count"],
            "average_ticket_cents": (
                int(summary["total_sales_cents"] / summary["paid_ticket_count"])
                if summary["paid_ticket_count"]
                else 0
            ),
            "note": cash_shift.closing_note,
        }
    )
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type=PrintJobType.CASH_SHIFT,
        printer_id=printer.id,
        printer_key_snapshot="CAJA",
        cash_shift_id=cash_shift.id,
        content_snapshot=sanitize_print_content(content),
        status=PrintStatus.PENDING,
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
    """Encola una cancelacion de comanda idempotente para una linea enviada."""
    existing = db.execute(
        select(PrintJob).where(PrintJob.idempotency_key == idempotency_key)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    if line.station_id_snapshot is None:
        raise BusinessConflictError("La linea no tiene estacion para cancelar.")
    station = db.get(ProductionStation, line.station_id_snapshot)
    if station is None:
        raise EntityNotFoundError("La estacion de la linea no existe.")
    if not station.printer_key:
        raise BusinessConflictError(
            f"La estacion {station.name} no tiene impresora configurada."
        )
    printer = get_active_printer(db, station.printer_key)
    station_order_id = db.execute(
        select(StationOrder.id)
        .join(StationOrderLine, StationOrderLine.station_order_id == StationOrder.id)
        .where(StationOrderLine.ticket_line_id == line.id)
        .order_by(StationOrder.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    print_job = PrintJob(
        folio=generate_folio(db, "IMPRESION"),
        job_type=PrintJobType.COMMAND_CANCELLATION,
        printer_id=printer.id,
        printer_key_snapshot=printer.printer_key,
        ticket_id=ticket.id,
        cash_shift_id=ticket.cash_shift_id,
        station_order_id=station_order_id,
        content_snapshot=build_cancellation_content(ticket, station, line, reason),
        status=PrintStatus.PENDING,
        attempts=0,
        idempotency_key=idempotency_key,
    )
    db.add(print_job)
    db.flush()
    return print_job
