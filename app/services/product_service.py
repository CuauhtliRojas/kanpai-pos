import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditEvent,
    Employee,
    Product,
    ProductPackage,
    ProductPackageItem,
    ProductStationAssignment,
    Ticket,
    TicketDiscount,
    TicketLine,
)
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)

CHARGEABLE_LINE_TYPES = ("SIMPLE", "PACKAGE_PARENT")
CANCELLED_LINE_STATUSES = ("CANCELLED", "CANCELED", "CANCELADO")


def list_pos_products(db: Session) -> list[Product]:
    """Lista productos activos y visibles disponibles para captura en POS."""
    return list(
        db.execute(
            select(Product)
            .where(Product.active.is_(True), Product.visible_pos.is_(True))
            .order_by(Product.display_name, Product.id)
        ).scalars()
    )


def get_ticket_lines(db: Session, ticket_id: int) -> list[TicketLine]:
    """Obtiene las líneas de un ticket en el orden en que fueron creadas."""
    if db.get(Ticket, ticket_id) is None:
        raise EntityNotFoundError("El ticket no existe.")
    return list(
        db.execute(
            select(TicketLine)
            .where(TicketLine.ticket_id == ticket_id)
            .order_by(TicketLine.id)
        ).scalars()
    )


def _primary_station_id(db: Session, product_id: int) -> int | None:
    return db.execute(
        select(ProductStationAssignment.station_id)
        .where(
            ProductStationAssignment.product_id == product_id,
            ProductStationAssignment.is_primary.is_(True),
            ProductStationAssignment.active.is_(True),
        )
        .order_by(ProductStationAssignment.id)
        .limit(1)
    ).scalar_one_or_none()


def _line_from_product(
    *,
    ticket: Ticket,
    product: Product,
    employee_id: int,
    quantity: int,
    station_id: int | None,
    line_type: str,
    unit_price_cents: int,
    price_mode: str,
    note: str | None = None,
    package_id: int | None = None,
    package_item_id: int | None = None,
    parent_ticket_line_id: int | None = None,
) -> TicketLine:
    return TicketLine(
        ticket_id=ticket.id,
        parent_ticket_line_id=parent_ticket_line_id,
        package_id=package_id,
        package_item_id=package_item_id,
        product_id=product.id,
        line_type=line_type,
        quantity=quantity,
        unit_price_cents=unit_price_cents,
        line_total_cents=unit_price_cents * quantity,
        price_mode=price_mode,
        product_name_snapshot=product.display_name,
        product_sku_snapshot=product.sku,
        category_id_snapshot=product.category_id,
        station_id_snapshot=station_id,
        note=note,
        status="CAPTURED",
        created_by_employee_id=employee_id,
    )


def _recalculate_ticket_totals(db: Session, ticket: Ticket) -> None:
    """Recalcula importes cobrables sin sumar componentes incluidos."""
    subtotal = db.execute(
        select(func.coalesce(func.sum(TicketLine.line_total_cents), 0)).where(
            TicketLine.ticket_id == ticket.id,
            TicketLine.line_type.in_(CHARGEABLE_LINE_TYPES),
            TicketLine.status.not_in(CANCELLED_LINE_STATUSES),
        )
    ).scalar_one()
    discount = db.execute(
        select(func.coalesce(func.sum(TicketDiscount.amount_cents), 0)).where(
            TicketDiscount.ticket_id == ticket.id
        )
    ).scalar_one()

    ticket.subtotal_cents = int(subtotal)
    ticket.discount_cents = int(discount)
    ticket.total_cents = max(
        ticket.subtotal_cents - ticket.discount_cents + ticket.tax_cents,
        0,
    )


def add_product_to_ticket(
    db: Session,
    ticket_id: int,
    product_id: int,
    employee_id: int,
    quantity: int,
    note: str | None = None,
) -> list[TicketLine]:
    """Agrega un producto simple o paquete a un ticket abierto.

    Valida las entidades y reglas de captura, genera snapshots inmutables,
    recalcula los totales y registra auditoría. La operación hace ``flush``
    pero nunca ``commit``; el dueño de la transacción decide confirmar o
    revertir todos los cambios.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    if ticket.status.upper() != "OPEN":
        raise BusinessConflictError("El ticket no está abierto para captura.")

    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError("El empleado no existe.")
    if not employee.active:
        raise BusinessConflictError("El empleado está inactivo.")

    product = db.get(Product, product_id)
    if product is None:
        raise EntityNotFoundError("El producto no existe.")
    if not product.active:
        raise InvalidBusinessDataError("El producto está inactivo.")
    if not product.visible_pos:
        raise InvalidBusinessDataError("El producto no está visible en POS.")
    if product.price_cents <= 0:
        raise InvalidBusinessDataError("El producto debe tener un precio mayor a cero.")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise InvalidBusinessDataError("La cantidad debe ser un entero positivo.")

    lines: list[TicketLine] = []
    event_type = "TICKET_LINE_ADDED"
    if product.product_type.upper() == "PACKAGE":
        package = db.execute(
            select(ProductPackage).where(
                ProductPackage.package_product_id == product.id,
                ProductPackage.active.is_(True),
            )
        ).scalar_one_or_none()
        if package is None:
            raise InvalidBusinessDataError("El paquete no tiene configuración activa.")
        package_items = list(
            db.execute(
                select(ProductPackageItem)
                .where(
                    ProductPackageItem.package_id == package.id,
                    ProductPackageItem.active.is_(True),
                )
                .order_by(ProductPackageItem.sort_order, ProductPackageItem.id)
            ).scalars()
        )
        if not package_items:
            raise InvalidBusinessDataError("El paquete no tiene componentes activos.")

        parent = _line_from_product(
            ticket=ticket,
            product=product,
            employee_id=employee_id,
            quantity=quantity,
            station_id=_primary_station_id(db, product.id),
            line_type="PACKAGE_PARENT",
            unit_price_cents=product.price_cents,
            price_mode="PACKAGE_PRICE",
            note=note,
            package_id=package.id,
        )
        db.add(parent)
        db.flush()
        lines.append(parent)

        for item in package_items:
            if item.quantity <= 0:
                raise InvalidBusinessDataError(
                    "El paquete contiene una cantidad de componente inválida."
                )
            component = db.get(Product, item.component_product_id)
            if component is None or not component.active:
                raise InvalidBusinessDataError(
                    "El paquete contiene un producto inexistente o inactivo."
                )
            component_line = _line_from_product(
                ticket=ticket,
                product=component,
                employee_id=employee_id,
                quantity=item.quantity * quantity,
                station_id=(
                    item.station_id_override
                    if item.station_id_override is not None
                    else _primary_station_id(db, component.id)
                ),
                line_type="PACKAGE_COMPONENT",
                unit_price_cents=0,
                price_mode="INCLUDED_IN_PACKAGE",
                package_id=package.id,
                package_item_id=item.id,
                parent_ticket_line_id=parent.id,
            )
            db.add(component_line)
            lines.append(component_line)
        event_type = "PACKAGE_LINE_ADDED"
    else:
        line = _line_from_product(
            ticket=ticket,
            product=product,
            employee_id=employee_id,
            quantity=quantity,
            station_id=_primary_station_id(db, product.id),
            line_type="SIMPLE",
            unit_price_cents=product.price_cents,
            price_mode="NORMAL",
            note=note,
        )
        db.add(line)
        lines.append(line)

    db.flush()
    _recalculate_ticket_totals(db, ticket)
    db.add(
        AuditEvent(
            event_type=event_type,
            entity_type="TicketLine",
            entity_id=lines[0].id,
            actor_employee_id=employee_id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            after_snapshot=json.dumps(
                {
                    "product_id": product.id,
                    "quantity": quantity,
                    "line_ids": [line.id for line in lines],
                    "total_cents": ticket.total_cents,
                }
            ),
        )
    )
    db.flush()
    return lines
