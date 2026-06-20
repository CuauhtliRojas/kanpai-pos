from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.models import DiningTable, Employee

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/tables")
def list_tables(db: Session = Depends(get_db)) -> list[dict]:
    tables = (
        db.execute(
            select(DiningTable)
            .where(DiningTable.active.is_(True))
            .order_by(DiningTable.sort_order, DiningTable.table_code)
        )
        .scalars()
        .all()
    )

    return [
        {
            "id": table.id,
            "table_code": table.table_code,
            "display_name": table.display_name,
            "buzzer_number": table.buzzer_number,
            "status": table.status_cache,
            "active": table.active,
        }
        for table in tables
    ]


@router.get("/employees")
def list_employees(db: Session = Depends(get_db)) -> list[dict]:
    employees = (
        db.execute(select(Employee).order_by(Employee.employee_code)).scalars().all()
    )

    return [
        {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "full_name": employee.full_name,
            "pos_alias": employee.pos_alias,
            "active": employee.active,
            "sync_status": employee.sync_status,
        }
        for employee in employees
    ]
