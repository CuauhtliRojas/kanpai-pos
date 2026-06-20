from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models import MenuCategory, PaymentMethod, ProductionStation
from app.schemas import ProductResponse
from app.services.product_service import list_pos_products

router = APIRouter(prefix="/catalog", tags=["catalog"])


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
            select(MenuCategory).order_by(MenuCategory.sort_order, MenuCategory.name)
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
            )
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
