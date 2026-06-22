from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.models import DiscountPreset, MenuCategory, PaymentMethod, Product, ProductVariantGroup, ProductionStation
from app.schemas import ProductResponse
from app.schemas.discount import DiscountPresetResponse
from app.schemas.variant import VariantGroupResponse
from app.services.product_service import list_pos_products

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/discount-presets", response_model=list[DiscountPresetResponse])
def list_discount_presets(
    db: Session = Depends(get_db),
) -> list[DiscountPresetResponse]:
    presets = db.scalars(
        select(DiscountPreset)
        .where(
            DiscountPreset.active.is_(True),
            DiscountPreset.visible_pos.is_(True),
        )
        .order_by(DiscountPreset.sort_order, DiscountPreset.name)
    ).all()
    return [DiscountPresetResponse.model_validate(preset) for preset in presets]


@router.get("/variant-groups", response_model=list[VariantGroupResponse])
def list_variant_groups(db: Session = Depends(get_db)) -> list[VariantGroupResponse]:
    groups = db.scalars(
        select(ProductVariantGroup)
        .options(selectinload(ProductVariantGroup.options))
        .where(ProductVariantGroup.active.is_(True))
        .order_by(ProductVariantGroup.id)
    ).all()
    return [VariantGroupResponse.model_validate(group) for group in groups]


@router.get("/products/{product_id}/variant-groups", response_model=list[VariantGroupResponse])
def product_variant_groups(product_id: int, db: Session = Depends(get_db)) -> list[VariantGroupResponse]:
    if db.get(Product, product_id) is None:
        raise HTTPException(status_code=404, detail="El producto no existe.")
    groups = db.scalars(
        select(ProductVariantGroup)
        .options(selectinload(ProductVariantGroup.options))
        .where(ProductVariantGroup.product_id == product_id, ProductVariantGroup.active.is_(True))
        .order_by(ProductVariantGroup.id)
    ).all()
    return [VariantGroupResponse.model_validate(group) for group in groups]


@router.get("/products", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)) -> list[ProductResponse]:
    """Expone el catálogo activo y visible para captura en POS."""
    return [
        ProductResponse.model_validate(product) for product in list_pos_products(db)
    ]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> list[dict]:
    categories = (
        db.execute(
            select(MenuCategory)
            .where(MenuCategory.active.is_(True))
            .order_by(MenuCategory.sort_order, MenuCategory.name)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": category.id,
            "name": category.name,
            "sort_order": category.sort_order,
            "active": category.active,
            "sync_status": category.sync_status,
        }
        for category in categories
    ]


@router.get("/stations")
def list_stations(db: Session = Depends(get_db)) -> list[dict]:
    stations = (
        db.execute(
            select(ProductionStation).order_by(
                ProductionStation.sort_order,
                ProductionStation.name,
            ).where(ProductionStation.active.is_(True))
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": station.id,
            "station_key": station.station_key,
            "name": station.name,
            "printer_key": station.printer_key,
            "sort_order": station.sort_order,
            "active": station.active,
            "sync_status": station.sync_status,
        }
        for station in stations
    ]


@router.get("/payment-methods")
def list_payment_methods(db: Session = Depends(get_db)) -> list[dict]:
    methods = (
        db.execute(select(PaymentMethod).order_by(PaymentMethod.id)).scalars().all()
    )

    return [
        {
            "id": method.id,
            "method_key": method.method_key,
            "name": method.name,
            "requires_reference": method.requires_reference,
            "active": method.active,
        }
        for method in methods
    ]
