import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.constants import (
    PriceMode,
    ProductType,
    TicketLineStatus,
    TicketLineType,
    TicketStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    Employee,
    Product,
    ProductPackage,
    ProductPackageItem,
    ProductStationAssignment,
    ProductVariantGroup,
    ProductVariantOption,
    Ticket,
    TicketLine,
    TicketLineVariantSelection,
)
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.ticket_service import recalculate_ticket_totals

CHARGEABLE_LINE_TYPES = (TicketLineType.SIMPLE, TicketLineType.PACKAGE_PARENT)
CANCELLED_LINE_STATUSES = (TicketLineStatus.CANCELLED,)


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
        status=TicketLineStatus.CAPTURED,
        created_by_employee_id=employee_id,
    )


def add_product_to_ticket(
    db: Session,
    ticket_id: int,
    product_id: int,
    employee_id: int,
    quantity: int,
    note: str | None = None,
    variant_selections: list[dict] | None = None,
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
    if ticket.status != TicketStatus.OPEN:
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

    normalized_variants = variant_selections or []
    groups = list(db.scalars(select(ProductVariantGroup).where(
        ProductVariantGroup.product_id == product.id,
        ProductVariantGroup.active.is_(True),
    )))
    groups_by_id = {group.id: group for group in groups}
    counts = {group.id: 0 for group in groups}
    resolved_variants: list[tuple[ProductVariantGroup, ProductVariantOption, int]] = []
    for selection in normalized_variants:
        group = groups_by_id.get(selection["variant_group_id"])
        option = db.get(ProductVariantOption, selection["variant_option_id"])
        selected_quantity = selection.get("quantity", 1)
        if group is None or option is None or option.variant_group_id != group.id or not option.active:
            raise InvalidBusinessDataError("La opción de variante no pertenece al producto.")
        if isinstance(selected_quantity, bool) or selected_quantity <= 0:
            raise InvalidBusinessDataError("La cantidad de variante debe ser positiva.")
        counts[group.id] += selected_quantity
        resolved_variants.append((group, option, selected_quantity))
    for group in groups:
        minimum = max(group.min_select, 1 if group.required else 0)
        if counts[group.id] < minimum or counts[group.id] > group.max_select:
            raise InvalidBusinessDataError(
                f"El grupo {group.name} requiere entre {minimum} y {group.max_select} selecciones."
            )
    if normalized_variants and not groups:
        raise InvalidBusinessDataError("El producto no admite variantes.")

    variant_delta = sum(
        option.price_delta_cents * selected_quantity
        for _, option, selected_quantity in resolved_variants
    )
    lines: list[TicketLine] = []
    event_type = audit_event("TICKET_LINE_ADDED")
    if product.product_type == ProductType.PACKAGE:
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
            line_type=TicketLineType.PACKAGE_PARENT,
            unit_price_cents=product.price_cents + variant_delta,
            price_mode=PriceMode.PACKAGE_PRICE,
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
                line_type=TicketLineType.PACKAGE_COMPONENT,
                unit_price_cents=0,
                price_mode=PriceMode.INCLUDED_IN_PACKAGE,
                package_id=package.id,
                package_item_id=item.id,
                parent_ticket_line_id=parent.id,
            )
            db.add(component_line)
            lines.append(component_line)
        event_type = audit_event("PACKAGE_LINE_ADDED")
    else:
        line = _line_from_product(
            ticket=ticket,
            product=product,
            employee_id=employee_id,
            quantity=quantity,
            station_id=_primary_station_id(db, product.id),
            line_type=TicketLineType.SIMPLE,
            unit_price_cents=product.price_cents + variant_delta,
            price_mode=PriceMode.NORMAL,
            note=note,
        )
        db.add(line)
        lines.append(line)

    db.flush()
    for group, option, selected_quantity in resolved_variants:
        db.add(TicketLineVariantSelection(
            ticket_line_id=lines[0].id,
            variant_group_id=group.id,
            variant_option_id=option.id,
            quantity=selected_quantity,
            price_delta_cents_snapshot=option.price_delta_cents,
            name_snapshot=option.name,
            sku_snapshot=option.sku,
            station_id_snapshot=option.station_id,
        ))
    db.flush()
    recalculate_ticket_totals(db, ticket)
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
                    "variant_selections": [
                        {
                            "group_id": group.id,
                            "option_id": option.id,
                            "name": option.name,
                            "quantity": selected_quantity,
                        }
                        for group, option, selected_quantity in resolved_variants
                    ],
                }
            ),
        )
    )
    db.flush()
    return lines
