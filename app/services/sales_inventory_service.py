from datetime import datetime
from app.core.time import local_now_naive
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.constants import (
    InventoryMovementType,
    InventorySourceType,
    TicketLineStatus,
    TicketLineType,
    TicketStatus,
)
from app.models import (
    InventoryMovement,
    Product,
    ProductRecipe,
    ProductVariantGroup,
    ProductVariantOption,
    Ticket,
    TicketLine,
    TicketLineVariantSelection,
)
from app.services.exceptions import BusinessConflictError, EntityNotFoundError
from app.services.inventory_service import create_inventory_movement

CONSUMABLE_LINE_TYPES = (TicketLineType.SIMPLE, TicketLineType.PACKAGE_COMPONENT)
CANCELLED_LINE_STATUSES = (TicketLineStatus.CANCELLED,)


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
    if ticket.status != TicketStatus.PAID:
        raise BusinessConflictError("El inventario solo se consume en tickets pagados.")
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
    product_multipliers: dict[int, Decimal] = {}
    if lines:
        product_multipliers = {
            product.id: Decimal(product.inventory_recipe_multiplier or 1)
            for product in db.scalars(
                select(Product).where(
                    Product.id.in_({line.product_id for line in lines})
                )
            )
        }
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
                Decimal(recipe.waste_pct or 0)
            )
            quantity = (
                Decimal(line.quantity)
                * product_multipliers.get(line.product_id, Decimal("1"))
                * Decimal(recipe.quantity_base)
                * waste_multiplier
            )
            movements.append(
                create_inventory_movement(
                    db,
                    inventory_item_id=recipe.inventory_item_id,
                    movement_type=InventoryMovementType.SALE_CONSUMPTION,
                    quantity_base=quantity,
                    employee_id=employee_id,
                    reason=f"Venta ticket {ticket.folio}",
                    unit_cost_cents=recipe.inventory_item.unit_cost_cents,
                    source_type=InventorySourceType.TICKET_LINE,
                    source_id=line.id,
                    ticket_line_id=line.id,
                    require_adjust_permission=False,
                )
            )
        selections = db.scalars(
            select(TicketLineVariantSelection).where(
                TicketLineVariantSelection.ticket_line_id == line.id
            )
        )
        for selection in selections:
            option = db.get(ProductVariantOption, selection.variant_option_id)
            if option is None or option.product_id is None:
                continue
            option_recipes = db.scalars(
                select(ProductRecipe).where(
                    ProductRecipe.product_id == option.product_id,
                    ProductRecipe.active.is_(True),
                )
            )
            for recipe in option_recipes:
                option_product = db.get(Product, option.product_id)
                option_group = db.get(ProductVariantGroup, selection.variant_group_id)
                option_multiplier = (
                    Decimal("1")
                    if option_group is not None and option_group.name == "BROCHETAS"
                    else Decimal(option_product.inventory_recipe_multiplier or 1)
                )
                quantity = (
                    Decimal(line.quantity)
                    * Decimal(selection.quantity)
                    * option_multiplier
                    * Decimal(recipe.quantity_base)
                    * (Decimal("1") + Decimal(recipe.waste_pct or 0))
                )
                movements.append(
                    create_inventory_movement(
                        db,
                        inventory_item_id=recipe.inventory_item_id,
                        movement_type=InventoryMovementType.SALE_CONSUMPTION,
                        quantity_base=quantity,
                        employee_id=employee_id,
                        reason=f"Variante {selection.name_snapshot} ticket {ticket.folio}",
                        unit_cost_cents=recipe.inventory_item.unit_cost_cents,
                        source_type=InventorySourceType.VARIANT_OPTION,
                        source_id=selection.id,
                        ticket_line_id=line.id,
                        require_adjust_permission=False,
                    )
                )

    ticket.inventory_consumed_at = local_now_naive()
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
                InventoryMovement.movement_type
                == InventoryMovementType.SALE_CONSUMPTION,
                InventoryMovement.source_type == InventorySourceType.TICKET_LINE,
                InventoryMovement.source_id.in_(line_ids),
            )
            .order_by(InventoryMovement.id)
        )
    )
