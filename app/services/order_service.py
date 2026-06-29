from collections import defaultdict
from datetime import datetime
from app.core.time import local_now_naive

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.constants import (
    CommandValue,
    PrintJobType,
    PrintStatus,
    ProductionOrderStatus,
    TicketLineStatus,
    TicketLineType,
    TicketStatus,
    audit_event,
)
from app.models import (
    AuditEvent,
    CommandBatch,
    Employee,
    PrintJob,
    ProductStationAssignment,
    ProductionStation,
    StationOrder,
    StationOrderLine,
    Ticket,
    TicketLine,
)
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    InvalidBusinessDataError,
)
from app.services.folio_service import generate_folio
from app.services.print_service import build_command_content, get_active_printer

SENDABLE_LINE_TYPES = (TicketLineType.SIMPLE, TicketLineType.PACKAGE_COMPONENT)
SENDABLE_TICKET_STATUSES = (TicketStatus.OPEN, TicketStatus.IN_PAYMENT)


def _resolve_station(db: Session, line: TicketLine) -> ProductionStation | None:
    """Resuelve el snapshot de estación o la asignación primaria vigente."""
    snapshot_station = None
    if line.station_id_snapshot is not None:
        snapshot_station = db.get(ProductionStation, line.station_id_snapshot)
        if snapshot_station is None:
            raise EntityNotFoundError(
                f"La estación {line.station_id_snapshot} no existe."
            )
        if snapshot_station.active:
            return snapshot_station

    current_station = (
        db.execute(
            select(ProductionStation)
            .join(
                ProductStationAssignment,
                ProductStationAssignment.station_id == ProductionStation.id,
            )
            .where(
                ProductStationAssignment.product_id == line.product_id,
                ProductStationAssignment.is_primary.is_(True),
                ProductStationAssignment.active.is_(True),
                ProductionStation.active.is_(True),
            )
            .order_by(ProductStationAssignment.id.desc())
            .limit(1)
        )
        .scalars()
        .one_or_none()
    )
    if current_station is not None:
        return current_station

    if snapshot_station is not None:
        raise BusinessConflictError(
            f"La estación {snapshot_station.name} no está disponible."
        )

    return None



def send_round(db: Session, ticket_id: int, employee_id: int) -> CommandBatch:
    """Envía las líneas capturadas y genera comandas y trabajos lógicos.

    La función valida primero todas las estaciones e impresoras para evitar una
    ronda parcial. Después crea el lote, agrupa líneas producibles por estación,
    actualiza sus estados y registra auditoría. Hace ``flush`` para materializar
    identificadores, pero deja el ``commit`` al dueño de la transacción.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")

    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError("El empleado no existe.")
    if not employee.active:
        raise BusinessConflictError("El empleado está inactivo.")

    if ticket.status not in SENDABLE_TICKET_STATUSES:
        raise BusinessConflictError("El ticket no admite el envío de rondas.")

    captured_lines = list(
        db.execute(
            select(TicketLine)
            .where(
                TicketLine.ticket_id == ticket.id,
                TicketLine.status == TicketLineStatus.CAPTURED,
            )
            .order_by(TicketLine.id)
        ).scalars()
    )
    if not captured_lines:
        raise InvalidBusinessDataError("No hay líneas capturadas para enviar.")

    station_lines: dict[int, list[TicketLine]] = defaultdict(list)
    stations: dict[int, ProductionStation] = {}
    printers = {}
    for line in captured_lines:
        if line.line_type not in SENDABLE_LINE_TYPES:
            continue
        station = _resolve_station(db, line)
        if station is None:
            continue
        stations[station.id] = station
        station_lines[station.id].append(line)

    for station in stations.values():
        if not station.printer_key:
            raise BusinessConflictError(
                f"La estación {station.name} no tiene impresora configurada."
            )
        printers[station.id] = get_active_printer(
            db,
            station.printer_key,
            allow_inactive_in_development=True,
        )

    current_round = db.execute(
        select(func.coalesce(func.max(CommandBatch.round_number), 0)).where(
            CommandBatch.ticket_id == ticket.id
        )
    ).scalar_one()
    round_number = int(current_round) + 1
    batch = CommandBatch(
        ticket_id=ticket.id,
        round_number=round_number,
        batch_type=CommandValue.ORDER,
        created_by_employee_id=employee.id,
    )
    db.add(batch)
    db.flush()

    for station_id in sorted(station_lines):
        station = stations[station_id]
        lines = station_lines[station_id]
        station_order = StationOrder(
            command_batch_id=batch.id,
            ticket_id=ticket.id,
            station_id=station.id,
            folio=generate_folio(db, "COMANDA"),
            status=ProductionOrderStatus.QUEUED,
        )
        db.add(station_order)
        db.flush()

        for line in lines:
            db.add(
                StationOrderLine(
                    station_order_id=station_order.id,
                    ticket_line_id=line.id,
                    quantity=line.quantity,
                    product_name_snapshot=line.product_name_snapshot,
                    note_snapshot=line.note,
                    line_action=CommandValue.ADD,
                )
            )

        printer = printers[station_id]
        db.add(
            PrintJob(
                folio=generate_folio(db, "IMPRESION"),
                job_type=PrintJobType.COMMAND,
                printer_id=printer.id,
                printer_key_snapshot=printer.printer_key,
                ticket_id=ticket.id,
                station_order_id=station_order.id,
                command_batch_id=batch.id,
                content_snapshot=build_command_content(
                    ticket, station, round_number, lines
                ),
                status=PrintStatus.PENDING,
                attempts=0,
                idempotency_key=(
                    f"COMANDA:{batch.id}:STATION_ORDER:{station_order.id}"
                ),
            )
        )

    now = local_now_naive()
    station_line_ids = {line.id for lines in station_lines.values() for line in lines}
    for line in captured_lines:
        line.status = (
            TicketLineStatus.SENT_TO_KITCHEN
            if line.id in station_line_ids
            else TicketLineStatus.PRINTED
        )
        line.round_number = round_number
        line.sent_at = now

    db.add(
        AuditEvent(
            event_type=audit_event("ROUND_SENT"),
            entity_type="Ticket",
            entity_id=ticket.id,
            actor_employee_id=employee.id,
            cash_shift_id=ticket.cash_shift_id,
            ticket_id=ticket.id,
        )
    )
    db.flush()
    db.refresh(batch, attribute_names=["station_orders"])
    return batch


def list_ticket_station_orders(db: Session, ticket_id: int) -> list[StationOrder]:
    """Lista comandas de un ticket con sus líneas, en orden de creación."""
    if db.get(Ticket, ticket_id) is None:
        raise EntityNotFoundError("El ticket no existe.")
    return list(
        db.execute(
            select(StationOrder)
            .options(selectinload(StationOrder.lines))
            .where(StationOrder.ticket_id == ticket_id)
            .order_by(StationOrder.id)
        ).scalars()
    )
