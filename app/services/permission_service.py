from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmployeeRole, Permission, Role, RolePermission


def employee_has_permission(
    db: Session, employee_id: int, permission_key: str
) -> bool:
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
