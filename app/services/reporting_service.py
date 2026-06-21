from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.constants import (
    ActiveStatus,
    CashShiftStatus,
    InventoryMovementType,
    PrintStatus,
    StockAlertStatus,
    TicketLineStatus,
    TicketLineType,
    TicketStatus,
)
from app.models import (
    CashExpense,
    CashShift,
    InventoryItem,
    InventoryMovement,
    MenuCategory,
    Payment,
    PaymentMethod,
    PrintJob,
    ProductionStation,
    Product,
    StockAlert,
    Ticket,
    TicketLine,
    TicketLineVariantSelection,
    StationOrder,
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
            raise InvalidBusinessDataError(
                "date_from no puede ser posterior a date_to."
            )
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
            Ticket.status == TicketStatus.PAID, *paid_ticket_dates
        ),
    )
    total_paid = _sum(
        db,
        select(func.sum(Payment.amount_cents)).where(
            Payment.status == ActiveStatus.ACTIVE, *payment_dates
        ),
    )
    total_expenses = _sum(
        db,
        select(func.sum(CashExpense.amount_cents)).where(
            CashExpense.status == ActiveStatus.ACTIVE, *expense_dates
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
        db.scalar(
            select(func.count())
            .select_from(stock_totals)
            .where(stock_totals.c.quantity < 0)
        )
        or 0
    )
    return {
        "total_sales_cents": total_sales,
        "total_paid_cents": total_paid,
        "total_expenses_cents": total_expenses,
        "net_cash_cents": total_paid - total_expenses,
        "paid_ticket_count": _count(
            db, Ticket, Ticket.status == TicketStatus.PAID, *paid_ticket_dates
        ),
        "cancelled_ticket_count": _count(
            db, Ticket, Ticket.status == TicketStatus.CANCELLED, *cancelled_ticket_dates
        ),
        "open_ticket_count": _count(
            db, Ticket, Ticket.status == TicketStatus.OPEN, *ticket_dates
        ),
        "in_payment_ticket_count": _count(
            db, Ticket, Ticket.status == TicketStatus.IN_PAYMENT, *ticket_dates
        ),
        "active_cash_shift_count": _count(
            db, CashShift, CashShift.status == CashShiftStatus.OPEN, *shift_dates
        ),
        "pending_print_jobs_count": _count(
            db, PrintJob, PrintJob.status == PrintStatus.PENDING, *print_dates
        ),
        "failed_print_jobs_count": _count(
            db, PrintJob, PrintJob.status == PrintStatus.FAILED, *print_dates
        ),
        "low_stock_alert_count": _count(
            db, StockAlert, StockAlert.status == StockAlertStatus.OPEN, *alert_dates
        ),
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
        .where(Payment.status == ActiveStatus.ACTIVE, *dates)
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
            Ticket.status == TicketStatus.PAID,
            TicketLine.status != TicketLineStatus.CANCELLED,
            TicketLine.line_type.in_(
                (TicketLineType.SIMPLE, TicketLineType.PACKAGE_PARENT)
            ),
            *dates,
        )
        .group_by(
            TicketLine.product_id,
            sku,
            TicketLine.product_name_snapshot,
        )
        .order_by(TicketLine.product_id)
    ).all()
    result = []
    for row in rows:
        variant_rows = db.execute(
            select(
                TicketLineVariantSelection.name_snapshot,
                TicketLineVariantSelection.sku_snapshot,
                func.sum(TicketLineVariantSelection.quantity * TicketLine.quantity),
            )
            .join(TicketLine, TicketLine.id == TicketLineVariantSelection.ticket_line_id)
            .join(Ticket, Ticket.id == TicketLine.ticket_id)
            .where(
                TicketLine.product_id == row[0],
                Ticket.status == TicketStatus.PAID,
                TicketLine.status != TicketLineStatus.CANCELLED,
                *dates,
            )
            .group_by(
                TicketLineVariantSelection.name_snapshot,
                TicketLineVariantSelection.sku_snapshot,
            )
            .order_by(TicketLineVariantSelection.name_snapshot)
        ).all()
        result.append({
            "product_id": row[0],
            "sku": row[1],
            "product_name": row[2],
            "quantity_sold": int(row[3]),
            "total_cents": int(row[4]),
            "variant_breakdown": [
                {"name": variant[0], "sku": variant[1], "quantity_sold": int(variant[2])}
                for variant in variant_rows
            ],
        })
    return result


def get_sales_by_category(
    db: Session,
    date_from: str | None = None,
    date_to: str | None = None,
    cash_shift_id: int | None = None,
    category_id: int | None = None,
) -> list[dict]:
    """Agrupa lineas cobradas por la categoria capturada al vender.

    El descuento del ticket se prorratea en centavos entre sus categorias para
    conservar exactamente el total descontado. Los componentes informativos de
    paquetes siguen la misma exclusion que el reporte por producto.
    """
    dates = _date_conditions(
        func.coalesce(Ticket.paid_at, Ticket.created_at),
        parse_date_range(date_from, date_to),
    )
    conditions = [
        Ticket.status == TicketStatus.PAID,
        TicketLine.status != TicketLineStatus.CANCELLED,
        TicketLine.line_type.in_(
            (TicketLineType.SIMPLE, TicketLineType.PACKAGE_PARENT)
        ),
        *dates,
    ]
    if cash_shift_id is not None:
        conditions.append(Ticket.cash_shift_id == cash_shift_id)

    rows = db.execute(
        select(
            Ticket.id,
            TicketLine.category_id_snapshot,
            func.coalesce(MenuCategory.name, "Sin categoria"),
            func.sum(TicketLine.quantity),
            func.sum(TicketLine.line_total_cents),
            Ticket.discount_cents,
        )
        .join(TicketLine, TicketLine.ticket_id == Ticket.id)
        .outerjoin(MenuCategory, MenuCategory.id == TicketLine.category_id_snapshot)
        .where(*conditions)
        .group_by(
            Ticket.id,
            TicketLine.category_id_snapshot,
            MenuCategory.name,
            Ticket.discount_cents,
        )
        .order_by(Ticket.id, TicketLine.category_id_snapshot)
    ).all()

    by_ticket: dict[int, list] = {}
    for row in rows:
        by_ticket.setdefault(row[0], []).append(row)

    totals: dict[tuple[int | None, str], dict] = {}
    for ticket_id, ticket_rows in by_ticket.items():
        ticket_gross = sum(int(row[4] or 0) for row in ticket_rows)
        ticket_discount = min(int(ticket_rows[0][5] or 0), ticket_gross)
        allocated = 0
        for index, row in enumerate(ticket_rows):
            gross = int(row[4] or 0)
            if ticket_gross <= 0:
                discount = 0
            elif index == len(ticket_rows) - 1:
                discount = ticket_discount - allocated
            else:
                discount = ticket_discount * gross // ticket_gross
                allocated += discount
            key = (row[1], str(row[2]))
            item = totals.setdefault(
                key,
                {
                    "category_id": row[1],
                    "category_name": str(row[2]),
                    "gross_sales_cents": 0,
                    "net_sales_cents": 0,
                    "discount_cents": 0,
                    "quantity_sold": Decimal("0"),
                    "ticket_ids": set(),
                },
            )
            item["gross_sales_cents"] += gross
            item["discount_cents"] += discount
            item["net_sales_cents"] += gross - discount
            item["quantity_sold"] += Decimal(row[3] or 0)
            item["ticket_ids"].add(ticket_id)

    total_net = sum(item["net_sales_cents"] for item in totals.values())
    result = []
    for item in totals.values():
        ticket_ids = item.pop("ticket_ids")
        item["ticket_count"] = len(ticket_ids)
        item["share_bps"] = (
            round(item["net_sales_cents"] * 10_000 / total_net)
            if total_net > 0
            else None
        )
        if category_id is None or item["category_id"] == category_id:
            result.append(item)
    return sorted(result, key=lambda item: (-item["net_sales_cents"], item["category_name"]))


def get_inventory_consumption(
    db: Session,
    movement_type: str = InventoryMovementType.SALE_CONSUMPTION,
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
        "reprint_count": _count(
            db, PrintJob, PrintJob.idempotency_key.like("REPRINT:%"), *dates
        ),
        "pending_count": status_counts.get(PrintStatus.PENDING, 0),
        "claimed_count": status_counts.get(PrintStatus.CLAIMED, 0),
        "printed_count": status_counts.get(PrintStatus.PRINTED, 0),
        "failed_count": status_counts.get(PrintStatus.FAILED, 0),
        "cancelled_count": status_counts.get(TicketStatus.CANCELLED, 0),
        "by_printer": by_printer,
        "by_job_type": by_job_type,
    }


def get_production_times(
    db: Session, date_from: str | None = None, date_to: str | None = None
) -> list[dict]:
    """Average production intervals per station using only complete pairs."""
    conditions = _date_conditions(
        StationOrder.created_at, parse_date_range(date_from, date_to)
    )
    orders = list(
        db.scalars(select(StationOrder).where(*conditions).order_by(StationOrder.id))
    )
    station_ids = sorted({order.station_id for order in orders})
    stations = {
        station.id: station
        for station in db.scalars(
            select(ProductionStation).where(ProductionStation.id.in_(station_ids))
        )
    } if station_ids else {}

    def average(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    result = []
    for station_id in station_ids:
        station_orders = [order for order in orders if order.station_id == station_id]
        receive = [
            (order.received_at - order.created_at).total_seconds()
            for order in station_orders
            if order.received_at is not None
        ]
        prepare = [
            (order.completed_at - order.started_at).total_seconds()
            for order in station_orders
            if order.started_at is not None and order.completed_at is not None
        ]
        total = [
            (order.delivered_at - order.created_at).total_seconds()
            for order in station_orders
            if order.delivered_at is not None
        ]
        result.append(
            {
                "station_id": station_id,
                "station_name": stations[station_id].name,
                "orders_count": len(station_orders),
                "average_receive_seconds": average(receive),
                "average_prepare_seconds": average(prepare),
                "average_total_service_seconds": average(total),
            }
        )
    return result
