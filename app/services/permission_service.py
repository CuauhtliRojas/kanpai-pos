from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employee, EmployeeRole, Permission, Role, RolePermission
from app.services.exceptions import (
    BusinessConflictError,
    EntityNotFoundError,
    PermissionDeniedError,
)


def employee_has_permission(db: Session, employee_id: int, permission_key: str) -> bool:
    """Valida que un empleado tenga un rol y permiso activos para una operación.

    La consulta usa las tablas de asignación reales y no concede permisos por
    nombre de empleado ni por una clave de rol implícita.
    """
    permission_id = db.execute(
        select(Permission.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(EmployeeRole, EmployeeRole.role_id == Role.id)
        .where(
            EmployeeRole.employee_id == employee_id,
            Permission.permission_key == permission_key,
            Permission.active.is_(True),
            Role.active.is_(True),
        )
        .limit(1)
    ).scalar_one_or_none()
    return permission_id is not None


def require_employee_permission(
    db: Session, employee_id: int, permission_key: str
) -> None:
    """Exige un permiso normalizado o levanta un error público de autorización."""
    if not employee_has_permission(db, employee_id, permission_key):
        raise PermissionDeniedError(f"El empleado no tiene permiso {permission_key}.")


def get_active_employee(db: Session, employee_id: int) -> Employee:
    """Obtiene un empleado activo con errores de dominio estables."""
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError("El empleado no existe.")
    if not employee.active:
        raise BusinessConflictError("El empleado está inactivo.")
    return employee
