from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_db
from app.api.security import require_admin_read_permission
from app.domain.constants import TableStatus, TicketStatus
from app.models import DiningTable, Employee, Ticket
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

    active_tickets = (
        db.execute(
            select(Ticket)
            .where(
                Ticket.table_id.in_([table.id for table in tables]),
                Ticket.status.in_((TicketStatus.OPEN, TicketStatus.IN_PAYMENT)),
            )
            .order_by(Ticket.table_id, Ticket.opened_at.desc(), Ticket.id.desc())
        )
        .scalars()
        .all()
    )
    active_ticket_by_table: dict[int, Ticket] = {}
    for ticket in active_tickets:
        active_ticket_by_table.setdefault(ticket.table_id, ticket)

    response = []
    for table in tables:
        active_ticket = active_ticket_by_table.get(table.id)
        effective_status = (
            TableStatus.IN_PAYMENT
            if active_ticket and active_ticket.status == TicketStatus.IN_PAYMENT
            else TableStatus.OCCUPIED
            if active_ticket
            else TableStatus.FREE
        )
        response.append(
            {
                "id": table.id,
                "table_code": table.table_code,
                "display_name": table.display_name,
                "buzzer_number": table.buzzer_number,
                "status": effective_status,
                "active": table.active,
                "active_ticket_id": active_ticket.id if active_ticket else None,
                "active_ticket_folio": active_ticket.folio if active_ticket else None,
                "active_ticket_status": active_ticket.status if active_ticket else None,
                "active_ticket_total_cents": (
                    active_ticket.total_cents if active_ticket else None
                ),
                "active_ticket_payment_status": (
                    active_ticket.payment_status if active_ticket else None
                ),
            }
        )
    return response


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


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeDetailResponse,
    dependencies=[Depends(require_admin_read_permission)],
    tags=["operations", "admin-read-only"],
    summary="Consultar empleado (admin)",
    description="Detalle administrativo read-only; nunca expone pin_hash.",
)
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
    dependencies=[Depends(require_admin_read_permission)],
    tags=["operations", "admin-read-only"],
    summary="Consultar permisos de empleado (admin)",
    description="Roles y permisos efectivos para consulta administrativa.",
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


@router.get(
    "/roles",
    response_model=list[RoleResponse],
    dependencies=[Depends(require_admin_read_permission)],
    tags=["operations", "admin-read-only"],
    summary="Listar roles (admin)",
    description="Catálogo read-only de roles y permisos asociados.",
)
def list_roles_endpoint(db: Session = Depends(get_db)) -> list[RoleResponse]:
    return [RoleResponse.model_validate(role) for role in list_roles(db)]


@router.get(
    "/permissions",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_admin_read_permission)],
    tags=["operations", "admin-read-only"],
    summary="Listar permisos (admin)",
    description="Catálogo read-only de permisos locales.",
)
def list_permissions_endpoint(db: Session = Depends(get_db)) -> list[PermissionResponse]:
    return [
        PermissionResponse.model_validate(permission)
        for permission in list_permissions(db)
    ]
