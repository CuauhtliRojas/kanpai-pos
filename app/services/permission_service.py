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


def _permission_dict(permission: Permission) -> dict:
    return {
        "id": permission.id,
        "permission_key": permission.permission_key,
        "description": permission.description,
        "active": permission.active,
    }


def list_permissions(db: Session) -> list[dict]:
    permissions = db.scalars(
        select(Permission).order_by(Permission.permission_key)
    ).all()
    return [_permission_dict(permission) for permission in permissions]


def _roles_with_permissions(db: Session, employee_id: int | None = None) -> list[dict]:
    role_query = select(Role)
    if employee_id is not None:
        role_query = role_query.join(
            EmployeeRole, EmployeeRole.role_id == Role.id
        ).where(EmployeeRole.employee_id == employee_id)
    roles = db.scalars(role_query.order_by(Role.role_key)).all()
    result = []
    for role in roles:
        permissions = db.scalars(
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role.id)
            .order_by(Permission.permission_key)
        ).all()
        result.append(
            {
                "id": role.id,
                "role_key": role.role_key,
                "name": role.name,
                "active": role.active,
                "permissions": [
                    _permission_dict(permission) for permission in permissions
                ],
            }
        )
    return result


def list_roles(db: Session) -> list[dict]:
    return _roles_with_permissions(db)


def get_employee_detail(db: Session, employee_id: int) -> dict:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise EntityNotFoundError("El empleado no existe.")
    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "full_name": employee.full_name,
        "pos_alias": employee.pos_alias,
        "active": employee.active,
        "sync_status": employee.sync_status,
        "pin_enabled": employee.pin_enabled,
        "last_login_at": employee.last_login_at,
        "roles": _roles_with_permissions(db, employee.id),
    }


def get_employee_permissions(db: Session, employee_id: int) -> dict:
    detail = get_employee_detail(db, employee_id)
    unique_permissions = {}
    for role in detail["roles"]:
        for permission in role["permissions"]:
            unique_permissions[permission["id"]] = permission
    return {
        "employee_id": employee_id,
        "roles": detail["roles"],
        "permissions": sorted(
            unique_permissions.values(), key=lambda item: item["permission_key"]
        ),
    }
