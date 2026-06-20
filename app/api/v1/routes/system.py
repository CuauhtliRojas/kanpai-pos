from sqlalchemy import select, text
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models import (
    BusinessSetting,
    DiningTable,
    Employee,
    MenuCategory,
    PaymentMethod,
    ProductionStation,
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/db")
def database_status(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "sqlite",
    }


@router.get("/seed-summary")
def seed_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    business_count = len(db.execute(select(BusinessSetting)).scalars().all())
    table_count = len(db.execute(select(DiningTable)).scalars().all())
    category_count = len(db.execute(select(MenuCategory)).scalars().all())
    station_count = len(db.execute(select(ProductionStation)).scalars().all())
    payment_method_count = len(db.execute(select(PaymentMethod)).scalars().all())
    employee_count = len(db.execute(select(Employee)).scalars().all())

    return {
        "business_settings": business_count,
        "tables": table_count,
        "categories": category_count,
        "stations": station_count,
        "payment_methods": payment_method_count,
        "employees": employee_count,
    }
