from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.models import DiningTable, Employee
from app.schemas.auth import (
    EmployeeDetailResponse,
    EmployeePermissionsResponse,
    PermissionResponse,
    RoleResponse,
)
from app.services.exceptions import EntityNotFoundError
from app.services.permission_service import (
    get_employee_detail,
    get_employee_permissions,
    list_permissions,
    list_roles,
)

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


@router.get("/employees/{employee_id}", response_model=EmployeeDetailResponse)
def get_employee_detail_endpoint(
    employee_id: int, db: Session = Depends(get_db)
) -> EmployeeDetailResponse:
    try:
        return EmployeeDetailResponse.model_validate(get_employee_detail(db, employee_id))
    except EntityNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from None


@router.get(
    "/employees/{employee_id}/permissions",
    response_model=EmployeePermissionsResponse,
)
def get_employee_permissions_endpoint(
    employee_id: int, db: Session = Depends(get_db)
) -> EmployeePermissionsResponse:
    try:
        return EmployeePermissionsResponse.model_validate(
            get_employee_permissions(db, employee_id)
        )
    except EntityNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from None


@router.get("/roles", response_model=list[RoleResponse])
def list_roles_endpoint(db: Session = Depends(get_db)) -> list[RoleResponse]:
    return [RoleResponse.model_validate(role) for role in list_roles(db)]


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions_endpoint(db: Session = Depends(get_db)) -> list[PermissionResponse]:
    return [
        PermissionResponse.model_validate(permission)
        for permission in list_permissions(db)
    ]
