from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CashExpense,
    CashShift,
    InventoryItem,
    InventoryMovement,
    Payment,
    PaymentMethod,
    PrintJob,
    Product,
    StockAlert,
    Ticket,
    TicketLine,
    Unit,
)
from app.services.exceptions import InvalidBusinessDataError


def parse_date_range(
    date_from: str | None, date_to: str | None
) -> tuple[datetime | None, datetime | None, bool]:
    """Convierte fechas ISO a límites SQL y valida que el rango sea coherente.

    El tercer valor indica si el límite superior es exclusivo. Una fecha sin hora
    incluye el día completo; un datetime conserva un límite superior inclusivo.
    """

    def parse(value: str, field: str) -> tuple[datetime, bool]:
        try:
            parsed_date = date.fromisoformat(value)
            return datetime.combine(parsed_date, time.min), True
        except ValueError:
            try:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is not None:
                    raise ValueError
                return parsed, False
            except ValueError as error:
                raise InvalidBusinessDataError(
                    f"{field} debe ser una fecha o datetime ISO local válido."
                ) from error

    start = parse(date_from, "date_from")[0] if date_from else None
    end = None
    end_exclusive = False
    if date_to:
        end, date_only = parse(date_to, "date_to")
        if date_only:
            end += timedelta(days=1)
            end_exclusive = True
    if start is not None and end is not None:
        invalid = start >= end if end_exclusive else start > end
        if invalid:
            raise InvalidBusinessDataError("date_from no puede ser posterior a date_to.")
    return start, end, end_exclusive


def _date_conditions(column, date_range: tuple[datetime | None, datetime | None, bool]):
    """Genera condiciones de rango reutilizables para timestamps operativos."""
    start, end, end_exclusive = date_range
    conditions = []
    if start is not None:
        conditions.append(column >= start)
    if end is not None:
        conditions.append(column < end if end_exclusive else column <= end)
    return conditions


def _sum(db: Session, statement) -> int:
    return int(db.scalar(statement) or 0)


def _count(db: Session, model, *conditions) -> int:
    return int(db.scalar(select(func.count(model.id)).where(*conditions)) or 0)


def get_operational_summary(
    db: Session, date_from: str | None = None, date_to: str | None = None
) -> dict:
    """Calcula indicadores operativos desde registros vigentes, sin snapshots."""
    date_range = parse_date_range(date_from, date_to)
    ticket_dates = _date_conditions(Ticket.created_at, date_range)
    paid_ticket_dates = _date_conditions(
        func.coalesce(Ticket.paid_at, Ticket.created_at), date_range
    )
    cancelled_ticket_dates = _date_conditions(
        func.coalesce(Ticket.cancelled_at, Ticket.created_at), date_range
    )
    payment_dates = _date_conditions(Payment.created_at, date_range)
    expense_dates = _date_conditions(CashExpense.created_at, date_range)
    print_dates = _date_conditions(PrintJob.created_at, date_range)
    shift_dates = _date_conditions(CashShift.opened_at, date_range)
    alert_dates = _date_conditions(StockAlert.opened_at, date_range)
    movement_dates = _date_conditions(InventoryMovement.created_at, date_range)

    total_sales = _sum(
        db,
        select(func.sum(Ticket.total_cents)).where(
            Ticket.status == "PAID", *paid_ticket_dates
        ),
    )
    total_paid = _sum(
        db,
        select(func.sum(Payment.amount_cents)).where(
            Payment.status == "ACTIVE", *payment_dates
        ),
    )
    total_expenses = _sum(
        db,
        select(func.sum(CashExpense.amount_cents)).where(
            CashExpense.status == "ACTIVE", *expense_dates
        ),
    )
    stock_totals = (
        select(
            InventoryMovement.inventory_item_id,
            func.sum(InventoryMovement.signed_quantity_base).label("quantity"),
        )
        .where(*movement_dates)
        .group_by(InventoryMovement.inventory_item_id)
        .subquery()
    )
    negative_items = int(
        db.scalar(select(func.count()).select_from(stock_totals).where(stock_totals.c.quantity < 0))
        or 0
    )
    return {
        "total_sales_cents": total_sales,
        "total_paid_cents": total_paid,
        "total_expenses_cents": total_expenses,
        "net_cash_cents": total_paid - total_expenses,
        "paid_ticket_count": _count(
            db, Ticket, Ticket.status == "PAID", *paid_ticket_dates
        ),
        "cancelled_ticket_count": _count(
            db, Ticket, Ticket.status == "CANCELLED", *cancelled_ticket_dates
        ),
        "open_ticket_count": _count(db, Ticket, Ticket.status == "OPEN", *ticket_dates),
        "in_payment_ticket_count": _count(db, Ticket, Ticket.status == "IN_PAYMENT", *ticket_dates),
        "active_cash_shift_count": _count(db, CashShift, CashShift.status == "OPEN", *shift_dates),
        "pending_print_jobs_count": _count(db, PrintJob, PrintJob.status == "PENDING", *print_dates),
        "failed_print_jobs_count": _count(db, PrintJob, PrintJob.status == "FAILED", *print_dates),
        "low_stock_alert_count": _count(db, StockAlert, StockAlert.status == "OPEN", *alert_dates),
        "inventory_negative_item_count": negative_items,
    }


def get_sales_by_payment_method(
    db: Session, date_from: str | None = None, date_to: str | None = None
) -> list[dict]:
    """Agrupa únicamente pagos activos por el método registrado."""
    dates = _date_conditions(Payment.created_at, parse_date_range(date_from, date_to))
    rows = db.execute(
        select(
            PaymentMethod.id,
            PaymentMethod.method_key,
            PaymentMethod.name,
            func.sum(Payment.amount_cents),
            func.count(Payment.id),
        )
        .join(Payment, Payment.payment_method_id == PaymentMethod.id)
        .where(Payment.status == "ACTIVE", *dates)
        .group_by(PaymentMethod.id, PaymentMethod.method_key, PaymentMethod.name)
        .order_by(PaymentMethod.id)
    ).all()
    return [
        {
            "payment_method_id": row[0],
            "method_key": row[1],
            "method_name": row[2],
            "total_cents": int(row[3]),
            "payment_count": int(row[4]),
        }
        for row in rows
    ]


def get_sales_by_product(
    db: Session, date_from: str | None = None, date_to: str | None = None
) -> list[dict]:
    """Agrupa venta monetaria pagada y excluye componentes informativos de paquetes."""
    dates = _date_conditions(
        func.coalesce(Ticket.paid_at, Ticket.created_at),
        parse_date_range(date_from, date_to),
    )
    sku = func.coalesce(TicketLine.product_sku_snapshot, Product.sku)
    rows = db.execute(
        select(
            TicketLine.product_id,
            sku,
            TicketLine.product_name_snapshot,
            func.sum(TicketLine.quantity),
            func.sum(TicketLine.line_total_cents),
        )
        .join(Ticket, Ticket.id == TicketLine.ticket_id)
        .join(Product, Product.id == TicketLine.product_id)
        .where(
            Ticket.status == "PAID",
            TicketLine.status != "CANCELLED",
            TicketLine.line_type.in_(("SIMPLE", "PACKAGE_PARENT")),
            *dates,
        )
        .group_by(
            TicketLine.product_id,
            sku,
            TicketLine.product_name_snapshot,
        )
        .order_by(TicketLine.product_id)
    ).all()
    return [
        {
            "product_id": row[0],
            "sku": row[1],
            "product_name": row[2],
            "quantity_sold": int(row[3]),
            "total_cents": int(row[4]),
        }
        for row in rows
    ]


def get_inventory_consumption(
    db: Session,
    movement_type: str = "SALE_CONSUMPTION",
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Agrupa cantidades absolutas de movimientos por insumo, unidad y tipo."""
    dates = _date_conditions(
        InventoryMovement.created_at, parse_date_range(date_from, date_to)
    )
    rows = db.execute(
        select(
            InventoryItem.id,
            InventoryItem.item_code,
            InventoryItem.name,
            InventoryMovement.movement_type,
            func.sum(InventoryMovement.quantity_base),
            Unit.name,
            func.count(InventoryMovement.id),
        )
        .join(InventoryItem, InventoryItem.id == InventoryMovement.inventory_item_id)
        .join(Unit, Unit.id == InventoryItem.base_unit_id)
        .where(InventoryMovement.movement_type == movement_type, *dates)
        .group_by(
            InventoryItem.id,
            InventoryItem.item_code,
            InventoryItem.name,
            InventoryMovement.movement_type,
            Unit.name,
        )
        .order_by(InventoryItem.id)
    ).all()
    return [
        {
            "inventory_item_id": row[0],
            "sku": row[1],
            "name": row[2],
            "movement_type": row[3],
            "total_quantity_base": Decimal(row[4]),
            "base_unit_name": row[5],
            "movement_count": int(row[6]),
        }
        for row in rows
    ]


def get_print_jobs_summary(
    db: Session, date_from: str | None = None, date_to: str | None = None
) -> dict:
    """Resume la cola por estado, impresora destino y tipo de documento."""
    dates = _date_conditions(PrintJob.created_at, parse_date_range(date_from, date_to))
    status_counts = dict(
        db.execute(
            select(PrintJob.status, func.count(PrintJob.id))
            .where(*dates)
            .group_by(PrintJob.status)
        ).all()
    )
    by_printer = dict(
        db.execute(
            select(PrintJob.printer_key_snapshot, func.count(PrintJob.id))
            .where(*dates)
            .group_by(PrintJob.printer_key_snapshot)
            .order_by(PrintJob.printer_key_snapshot)
        ).all()
    )
    by_job_type = dict(
        db.execute(
            select(PrintJob.job_type, func.count(PrintJob.id))
            .where(*dates)
            .group_by(PrintJob.job_type)
            .order_by(PrintJob.job_type)
        ).all()
    )
    return {
        "total_print_jobs": sum(status_counts.values()),
        "pending_count": status_counts.get("PENDING", 0),
        "claimed_count": status_counts.get("CLAIMED", 0),
        "printed_count": status_counts.get("PRINTED", 0),
        "failed_count": status_counts.get("FAILED", 0),
        "cancelled_count": status_counts.get("CANCELLED", 0),
        "by_printer": by_printer,
        "by_job_type": by_job_type,
    }
