import json
from datetime import datetime
from app.core.time import local_now_naive

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.constants import (
    PrintJobType,
    PrintStatus,
    TicketLineNoteType,
    TicketLineStatus,
    TicketLineType,
    TicketSplitStatus,
    TicketStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    PrintJob,
    Product,
    ProductVariantGroup,
    ProductVariantOption,
    ProductionStation,
    StationOrder,
    StationOrderLine,
    Ticket,
    TicketLine,
    TicketLineModification,
    TicketLineNote,
    TicketLineVariantSelection,
    TicketSplit,
    TicketSplitLine,
)
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.permission_service import get_active_employee
from app.services.print_service import build_modification_content, get_active_printer
from app.services.ticket_service import recalculate_ticket_totals


def _replace_variant_selections(
    db: Session,
    line: TicketLine,
    variant_selections: list[dict],
) -> int:
    """Delete existing variant selections, add new ones. Returns new unit_price_cents."""
    product = db.get(Product, line.product_id)
    if product is None:
        raise EntityNotFoundError("El producto de la línea no existe.")

    groups = list(
        db.scalars(
            select(ProductVariantGroup).where(
                ProductVariantGroup.product_id == product.id,
                ProductVariantGroup.active.is_(True),
            )
        )
    )
    groups_by_id = {g.id: g for g in groups}
    counts: dict[int, int] = {g.id: 0 for g in groups}
    resolved: list[tuple] = []

    if variant_selections and not groups:
        raise InvalidBusinessDataError("El producto no admite variantes de preparación.")

    for sel in variant_selections:
        group_id = sel["variant_group_id"]
        option_id = sel["variant_option_id"]
        qty = sel.get("quantity", 1)
        group = groups_by_id.get(group_id)
        option = db.get(ProductVariantOption, option_id)
        if (
            group is None
            or option is None
            or option.variant_group_id != group_id
            or not option.active
        ):
            raise InvalidBusinessDataError(
                "La opción de variante no pertenece al producto o no está activa."
            )
        if qty <= 0:
            raise InvalidBusinessDataError("La cantidad de cada variante debe ser positiva.")
        counts[group_id] = counts.get(group_id, 0) + qty
        resolved.append((group, option, qty))

    for group in groups:
        minimum = max(group.min_select, 1 if group.required else 0)
        actual = counts.get(group.id, 0)
        if actual < minimum or actual > group.max_select:
            raise InvalidBusinessDataError(
                f"El grupo '{group.name}' requiere entre {minimum} y {group.max_select} selecciones."
            )

    db.execute(
        sql_delete(TicketLineVariantSelection).where(
            TicketLineVariantSelection.ticket_line_id == line.id
        )
    )

    variant_delta = 0
    for group, option, qty in resolved:
        db.add(
            TicketLineVariantSelection(
                ticket_line_id=line.id,
                variant_group_id=group.id,
                variant_option_id=option.id,
                quantity=qty,
                price_delta_cents_snapshot=option.price_delta_cents,
                name_snapshot=option.name,
                sku_snapshot=option.sku,
                station_id_snapshot=option.station_id,
            )
        )
        variant_delta += option.price_delta_cents * qty

    db.flush()
    db.expire(line, ["variant_selections"])
    return product.price_cents + variant_delta


def modify_ticket_line(
    db: Session,
    line_id: int,
    employee_id: int,
    note: str | None = None,
    quantity: int | None = None,
    variant_selections: list[dict] | None = None,
) -> TicketLineModification:
    """Persist a line modification.

    Captured lines: quantity, variant_selections, and/or note can be changed; no print job.
    Sent/printed lines: note only (required); creates a station notice print job.
    """
    line = db.get(TicketLine, line_id)
    if line is None:
        raise EntityNotFoundError("La linea de ticket no existe.")
    ticket = db.get(Ticket, line.ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    if ticket.status not in (TicketStatus.OPEN, TicketStatus.IN_PAYMENT):
        raise BusinessConflictError("El ticket no admite modificaciones.")
    if line.status == TicketLineStatus.CANCELLED:
        raise BusinessConflictError("La linea cancelada no admite modificaciones.")
    employee = get_active_employee(db, employee_id)

    is_captured = line.status == TicketLineStatus.CAPTURED
    is_sent = line.status in (TicketLineStatus.SENT_TO_KITCHEN, TicketLineStatus.PRINTED)
    changing_captured_fields = quantity is not None or variant_selections is not None

    if changing_captured_fields and not is_captured:
        if quantity is not None:
            raise BusinessConflictError(
                "La línea ya fue enviada a cocina/barra. No se puede cambiar la cantidad. "
                "Solo puedes enviar una nota de modificación."
            )
        raise BusinessConflictError(
            "La preparación solo se puede cambiar antes de enviar la línea."
        )

    if changing_captured_fields:
        active_split_count = db.scalar(
            select(func.count(TicketSplitLine.id))
            .join(TicketSplit, TicketSplit.id == TicketSplitLine.ticket_split_id)
            .where(
                TicketSplitLine.ticket_line_id == line.id,
                TicketSplit.status != TicketSplitStatus.CANCELLED,
            )
        ) or 0
        if active_split_count > 0:
            raise BusinessConflictError(
                "Esta línea pertenece a una división activa. "
                "Cancela la división antes de cambiar la cantidad o preparación."
            )

    change_parts: list[str] = []
    before: dict = {}
    after: dict = {}
    needs_total_recalc = False

    if quantity is not None:
        old_qty = line.quantity
        if quantity != old_qty:
            line.quantity = quantity
            line.line_total_cents = line.unit_price_cents * quantity
            if line.line_type == TicketLineType.PACKAGE_PARENT:
                for child in db.scalars(
                    select(TicketLine).where(
                        TicketLine.parent_ticket_line_id == line.id,
                        TicketLine.status == TicketLineStatus.CAPTURED,
                    )
                ):
                    child.quantity = quantity
                    child.line_total_cents = child.unit_price_cents * quantity
            before["quantity"] = old_qty
            after["quantity"] = quantity
            change_parts.append(f"Cantidad: {old_qty} → {quantity}")
            needs_total_recalc = True

    if variant_selections is not None:
        new_unit_price = _replace_variant_selections(db, line, variant_selections)
        old_unit_price = line.unit_price_cents
        if new_unit_price != old_unit_price:
            before["unit_price_cents"] = old_unit_price
            after["unit_price_cents"] = new_unit_price
        line.unit_price_cents = new_unit_price
        line.line_total_cents = new_unit_price * line.quantity
        change_parts.append("Preparación actualizada")
        needs_total_recalc = True

    if needs_total_recalc:
        db.flush()
        recalculate_ticket_totals(db, ticket)
        db.flush()

    note_text = (note or "").strip()
    print_job = None

    if note is not None:
        if not note_text:
            if is_sent:
                raise InvalidBusinessDataError(
                    "Para líneas enviadas la nota es obligatoria."
                )
            # Captured line: empty note with other changes is fine; just skip note update
        else:
            line.note = note_text
            db.add(
                TicketLineNote(
                    ticket_line_id=line.id,
                    note_type=TicketLineNoteType.MODIFICATION,
                    note=note_text,
                    created_by_employee_id=employee.id,
                )
            )
            if is_sent:
                station_order = db.scalar(
                    select(StationOrder)
                    .join(StationOrderLine)
                    .where(StationOrderLine.ticket_line_id == line.id)
                    .order_by(StationOrder.id.desc())
                )
                if station_order is not None:
                    station = db.get(ProductionStation, station_order.station_id)
                    if station is None or not station.printer_key:
                        raise BusinessConflictError("La estacion no tiene impresora configurada.")
                    printer = get_active_printer(db, station.printer_key)
                    content = build_modification_content(
                        ticket, station, line, note_text
                    )
                    print_job = PrintJob(
                        folio=generate_folio(db, "IMPRESION"),
                        job_type=PrintJobType.MODIFICATION,
                        printer_id=printer.id,
                        printer_key_snapshot=printer.printer_key,
                        ticket_id=ticket.id,
                        station_order_id=station_order.id,
                        command_batch_id=station_order.command_batch_id,
                        content_snapshot=content,
                        status=PrintStatus.PENDING,
                        attempts=0,
                        idempotency_key=f"MODIFICACION:{line.id}:{local_now_naive().isoformat()}",
                    )
                    db.add(print_job)
                    db.flush()
            change_parts.append(note_text)

    if not change_parts:
        raise InvalidBusinessDataError("No hay cambios para guardar.")

    modification_note = " | ".join(change_parts)

    db.add(
        AuditEvent(
            event_type=audit_event("TICKET_LINE_MODIFIED"),
            entity_type="Linea de ticket",
            entity_id=line.id,
            actor_employee_id=employee.id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
            reason=modification_note,
            before_snapshot=json.dumps(before) if before else None,
            after_snapshot=json.dumps(after) if after else modification_note,
        )
    )
    modification = TicketLineModification(
        ticket_line_id=line.id,
        ticket_id=ticket.id,
        note=modification_note,
        created_by_employee_id=employee.id,
        print_job_id=print_job.id if print_job else None,
    )
    db.add(modification)
    db.flush()
    return modification
