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
    VariantOptionRecipe,
    TicketLine,
    TicketLineVariantSelection,
)
from app.services.exceptions import BusinessConflictError, EntityNotFoundError
from app.services.inventory_service import create_inventory_movement
from app.models.catalog import InventoryPreparation, PreparationRecipe

CONSUMABLE_LINE_TYPES = (TicketLineType.SIMPLE, TicketLineType.PACKAGE_COMPONENT)
CANCELLED_LINE_STATUSES = (TicketLineStatus.CANCELLED,)



def _rec03v_as_decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def _rec03v_model_attr(model, *names: str) -> str:
    for name in names:
        if hasattr(model, name):
            return name
    raise RuntimeError(
        f"No se encontro atributo esperado en {model.__name__}: {names}"
    )


def _create_sale_consumption_movements_expanding_preparations(
    db: Session,
    *,
    inventory_item_id: int,
    quantity_base: Decimal,
    employee_id: int,
    reason: str,
    source_type: InventorySourceType,
    source_id: int,
    ticket_line_id: int,
    unit_cost_cents: int | None,
    path: tuple[int, ...] = (),
) -> list[InventoryMovement]:
    """Crea movimientos de venta expandiendo insumos PREP-* a receta cruda.

    Si el insumo consumido es resultado de una preparacion activa, no descuenta
    el PREP como stock final; descuenta sus ingredientes en proporcion al
    rendimiento base. Soporta preparaciones anidadas y protege contra ciclos.
    """
    prep_result_attr = _rec03v_model_attr(
        InventoryPreparation,
        "result_inventory_item_id",
        "insumo_resultante_id",
    )
    prep_yield_attr = _rec03v_model_attr(
        InventoryPreparation,
        "yield_quantity_base",
        "rendimiento_cantidad_base",
    )
    prep_active_attr = _rec03v_model_attr(
        InventoryPreparation,
        "active",
        "activo",
    )

    recipe_prep_attr = _rec03v_model_attr(
        PreparationRecipe,
        "preparation_id",
        "preparacion_id",
    )
    recipe_item_attr = _rec03v_model_attr(
        PreparationRecipe,
        "inventory_item_id",
        "inventario_insumo_id",
    )
    recipe_qty_attr = _rec03v_model_attr(
        PreparationRecipe,
        "quantity_base",
        "cantidad_base",
    )
    recipe_active_attr = _rec03v_model_attr(
        PreparationRecipe,
        "active",
        "activo",
    )

    preparation = db.scalar(
        select(InventoryPreparation).where(
            getattr(InventoryPreparation, prep_result_attr) == inventory_item_id,
            getattr(InventoryPreparation, prep_active_attr).is_(True),
        )
    )

    if preparation is None:
        inventory_item = db.get(type(db.get(ProductRecipe, 0).inventory_item), inventory_item_id) if False else None
        return [
            create_inventory_movement(
                db,
                inventory_item_id=inventory_item_id,
                movement_type=InventoryMovementType.SALE_CONSUMPTION,
                quantity_base=quantity_base,
                employee_id=employee_id,
                reason=reason,
                unit_cost_cents=unit_cost_cents or 0,
                source_type=source_type,
                source_id=source_id,
                ticket_line_id=ticket_line_id,
                require_adjust_permission=False,
            )
        ]

    preparation_id = int(preparation.id)
    if preparation_id in path:
        raise BusinessConflictError("La receta de preparacion contiene un ciclo.")

    yield_quantity = _rec03v_as_decimal(getattr(preparation, prep_yield_attr))
    if yield_quantity <= 0:
        raise BusinessConflictError(
            "La preparacion no tiene rendimiento valido para consumir inventario."
        )

    child_recipes = list(
        db.scalars(
            select(PreparationRecipe)
            .where(
                getattr(PreparationRecipe, recipe_prep_attr) == preparation.id,
                getattr(PreparationRecipe, recipe_active_attr).is_(True),
            )
            .order_by(PreparationRecipe.id)
        )
    )
    if not child_recipes:
        raise BusinessConflictError(
            "La preparacion no tiene receta activa para consumir inventario."
        )

    factor = quantity_base / yield_quantity
    movements: list[InventoryMovement] = []

    for child_recipe in child_recipes:
        child_inventory_item_id = int(getattr(child_recipe, recipe_item_attr))
        child_waste_pct = _rec03v_as_decimal(getattr(child_recipe, "waste_pct", 0))
        child_quantity = (
            _rec03v_as_decimal(getattr(child_recipe, recipe_qty_attr))
            * factor
            * (Decimal("1") + child_waste_pct)
        )
        child_inventory_item = getattr(child_recipe, "inventory_item", None)
        child_unit_cost_cents = getattr(child_inventory_item, "unit_cost_cents", 0)

        movements.extend(
            _create_sale_consumption_movements_expanding_preparations(
                db,
                inventory_item_id=child_inventory_item_id,
                quantity_base=child_quantity,
                employee_id=employee_id,
                reason=reason,
                source_type=source_type,
                source_id=source_id,
                ticket_line_id=ticket_line_id,
                unit_cost_cents=child_unit_cost_cents,
                path=path + (preparation_id,),
            )
        )

    return movements


def consume_inventory_for_paid_ticket(
    db: Session, ticket_id: int, employee_id: int
) -> list[InventoryMovement]:
    """Genera una sola vez el consumo de recetas de un ticket pagado.

    Omite padres de paquete, lineas canceladas y productos sin receta. Cada
    receta activa produce movimientos negativos ligados a la linea. Si una
    receta consume una preparacion de inventario, esta se expande a sus insumos
    crudos usando el rendimiento base de la preparacion. El stock insuficiente
    se permite y el servicio de inventario actualiza su alerta. La funcion hace
    ``flush`` pero nunca ``commit``.
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
    recipes_by_variant_option: dict[int, list[VariantOptionRecipe]] = {}
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

        selection_option_ids = {
            selection.variant_option_id
            for selection in db.scalars(
                select(TicketLineVariantSelection).where(
                    TicketLineVariantSelection.ticket_line_id.in_(
                        {line.id for line in lines}
                    )
                )
            )
        }
        if selection_option_ids:
            option_recipes = db.scalars(
                select(VariantOptionRecipe)
                .where(
                    VariantOptionRecipe.variant_option_id.in_(selection_option_ids),
                    VariantOptionRecipe.active.is_(True),
                )
                .order_by(VariantOptionRecipe.id)
            )
            for recipe in option_recipes:
                recipes_by_variant_option.setdefault(
                    recipe.variant_option_id, []
                ).append(recipe)

    movements: list[InventoryMovement] = []
    for line in lines:
        for recipe in recipes_by_product.get(line.product_id, []):
            waste_multiplier = Decimal("1") + Decimal(recipe.waste_pct or 0)
            quantity = (
                Decimal(line.quantity)
                * product_multipliers.get(line.product_id, Decimal("1"))
                * Decimal(recipe.quantity_base)
                * waste_multiplier
            )
            movements.extend(
                _create_sale_consumption_movements_expanding_preparations(
                    db,
                    inventory_item_id=recipe.inventory_item_id,
                    quantity_base=quantity,
                    employee_id=employee_id,
                    reason=f"Venta ticket {ticket.folio}",
                    unit_cost_cents=recipe.inventory_item.unit_cost_cents,
                    source_type=InventorySourceType.TICKET_LINE,
                    source_id=line.id,
                    ticket_line_id=line.id,
                )
            )

        selections = db.scalars(
            select(TicketLineVariantSelection).where(
                TicketLineVariantSelection.ticket_line_id == line.id
            )
        )
        for selection in selections:
            option = db.get(ProductVariantOption, selection.variant_option_id)
            if option is None:
                continue

            if option.product_id is not None:
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
                    movements.extend(
                        _create_sale_consumption_movements_expanding_preparations(
                            db,
                            inventory_item_id=recipe.inventory_item_id,
                            quantity_base=quantity,
                            employee_id=employee_id,
                            reason=(
                                f"Variante {selection.name_snapshot} ticket {ticket.folio}"
                            ),
                            unit_cost_cents=recipe.inventory_item.unit_cost_cents,
                            source_type=InventorySourceType.VARIANT_OPTION,
                            source_id=selection.id,
                            ticket_line_id=line.id,
                        )
                    )

            for recipe in recipes_by_variant_option.get(selection.variant_option_id, []):
                quantity = (
                    Decimal(line.quantity)
                    * Decimal(selection.quantity)
                    * Decimal(recipe.quantity_base)
                    * (Decimal("1") + Decimal(recipe.waste_pct or 0))
                )
                movements.extend(
                    _create_sale_consumption_movements_expanding_preparations(
                        db,
                        inventory_item_id=recipe.inventory_item_id,
                        quantity_base=quantity,
                        employee_id=employee_id,
                        reason=(
                            f"Receta opcion {selection.name_snapshot} "
                            f"ticket {ticket.folio}"
                        ),
                        unit_cost_cents=recipe.inventory_item.unit_cost_cents,
                        source_type=InventorySourceType.VARIANT_OPTION,
                        source_id=selection.id,
                        ticket_line_id=line.id,
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
