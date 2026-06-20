from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryMovement, ProductRecipe, Ticket, TicketLine
from app.services.exceptions import BusinessConflictError, EntityNotFoundError
from app.services.inventory_service import create_inventory_movement

CONSUMABLE_LINE_TYPES = ("SIMPLE", "PACKAGE_COMPONENT")
CANCELLED_LINE_STATUSES = ("CANCELLED", "CANCELED", "CANCELADO")


def consume_inventory_for_paid_ticket(
    db: Session, ticket_id: int, employee_id: int
) -> list[InventoryMovement]:
    """Genera una sola vez el consumo de recetas de un ticket pagado.

    Omite padres de paquete, líneas canceladas y productos sin receta. Cada
    receta activa produce un movimiento negativo ligado a la línea. El stock
    insuficiente se permite y el servicio de inventario actualiza su alerta.
    La función hace ``flush`` pero nunca ``commit``.
    """
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise EntityNotFoundError("El ticket no existe.")
    if ticket.status != "PAID":
        raise BusinessConflictError(
            "El inventario solo se consume en tickets pagados."
        )
    if ticket.inventory_consumed_at is not None:
        return []

    lines = list(
        db.scalars(
            select(TicketLine)
            .where(
                TicketLine.ticket_id == ticket.id,
                TicketLine.line_type.in_(CONSUMABLE_LINE_TYPES),
                TicketLine.status.not_in(CANCELLED_LINE_STATUSES),
            )
            .order_by(TicketLine.id)
        )
    )
    recipes_by_product: dict[int, list[ProductRecipe]] = {}
    if lines:
        recipes = db.scalars(
            select(ProductRecipe)
            .where(
                ProductRecipe.product_id.in_({line.product_id for line in lines}),
                ProductRecipe.active.is_(True),
            )
            .order_by(ProductRecipe.id)
        )
        for recipe in recipes:
            recipes_by_product.setdefault(recipe.product_id, []).append(recipe)

    movements = []
    for line in lines:
        for recipe in recipes_by_product.get(line.product_id, []):
            waste_multiplier = Decimal("1") + (
                Decimal(recipe.waste_pct or 0) / Decimal("100")
            )
            quantity = (
                Decimal(line.quantity)
                * Decimal(recipe.quantity_base)
                * waste_multiplier
            )
            movements.append(
                create_inventory_movement(
                    db,
                    inventory_item_id=recipe.inventory_item_id,
                    movement_type="SALE_CONSUMPTION",
                    quantity_base=quantity,
                    employee_id=employee_id,
                    reason=f"Venta ticket {ticket.folio}",
                    unit_cost_cents=recipe.inventory_item.unit_cost_cents,
                    source_type="TICKET_LINE",
                    source_id=line.id,
                    ticket_line_id=line.id,
                    require_adjust_permission=False,
                )
            )

    ticket.inventory_consumed_at = datetime.utcnow()
    db.flush()
    return movements


def list_ticket_inventory_movements(
    db: Session, ticket_id: int
) -> list[InventoryMovement]:
    """Lista consumos de venta ligados a cualquiera de las líneas del ticket."""
    if db.get(Ticket, ticket_id) is None:
        raise EntityNotFoundError("El ticket no existe.")
    line_ids = select(TicketLine.id).where(TicketLine.ticket_id == ticket_id)
    return list(
        db.scalars(
            select(InventoryMovement)
            .where(
                InventoryMovement.movement_type == "SALE_CONSUMPTION",
                InventoryMovement.source_type == "TICKET_LINE",
                InventoryMovement.source_id.in_(line_ids),
            )
            .order_by(InventoryMovement.id)
        )
    )
