"""Autenticación local por PIN y sesiones revocables."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from app.core.time import local_now_naive

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.domain.constants import EmployeeSessionStatus
from app.models import Employee, EmployeeRole, EmployeeSession, Permission, Role, RolePermission
from app.services.exceptions import BusinessConflictError, EntityNotFoundError

PBKDF2_ITERATIONS = 310_000


def hash_pin(pin: str, salt: bytes | None = None) -> str:
    """Deriva un PIN con PBKDF2-SHA256 y salt aleatorio; nunca persiste el PIN."""
    if not pin or len(pin) < 4:
        raise ValueError("El PIN debe tener al menos cuatro caracteres.")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pin(pin: str, encoded: str) -> bool:
    """Valida en tiempo constante un PIN contra el formato PBKDF2 persistido."""
    try:
        algorithm, iterations, salt_hex, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", pin.encode(), bytes.fromhex(salt_hex), int(iterations)
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def login_with_pin(db: Session, employee_code: str, pin: str) -> EmployeeSession:
    """Autentica un empleado activo y crea una sesión local de duración limitada."""
    employee = db.scalar(select(Employee).where(Employee.employee_code == employee_code.strip()))
    if employee is None or not employee.active or not employee.pin_enabled or not employee.pin_hash:
        raise BusinessConflictError("Credenciales inválidas.")
    if not verify_pin(pin, employee.pin_hash):
        raise BusinessConflictError("Credenciales inválidas.")
    now = local_now_naive()
    employee.last_login_at = now
    session = EmployeeSession(
        employee_id=employee.id,
        session_token=secrets.token_urlsafe(32),
        status=EmployeeSessionStatus.ACTIVE,
        created_at=now,
        expires_at=now + timedelta(hours=get_settings().auth_session_hours),
    )
    db.add(session)
    db.flush()
    return session


def logout(db: Session, session_token: str) -> EmployeeSession:
    """Cierra de forma idempotente una sesión local existente."""
    session = db.scalar(select(EmployeeSession).where(EmployeeSession.session_token == session_token))
    if session is None:
        raise EntityNotFoundError("La sesión no existe.")
    if session.status == EmployeeSessionStatus.ACTIVE:
        session.status = EmployeeSessionStatus.CLOSED
        session.closed_at = local_now_naive()
        db.flush()
    return session


def get_session_identity(db: Session, session_token: str) -> tuple[Employee, list[str], list[str]]:
    """Resuelve empleado, roles y permisos; expira sesiones vencidas al consultarlas."""
    session = db.scalar(
        select(EmployeeSession)
        .options(selectinload(EmployeeSession.employee))
        .where(EmployeeSession.session_token == session_token)
    )
    if session is None:
        raise EntityNotFoundError("La sesión no existe.")
    if session.status == EmployeeSessionStatus.ACTIVE and session.expires_at <= local_now_naive():
        session.status = EmployeeSessionStatus.EXPIRED
        session.closed_at = local_now_naive()
        db.flush()
    if session.status != EmployeeSessionStatus.ACTIVE or not session.employee.active:
        raise BusinessConflictError("La sesión no está activa.")
    roles = list(db.scalars(
        select(Role.role_key).join(EmployeeRole).where(
            EmployeeRole.employee_id == session.employee_id, Role.active.is_(True)
        ).order_by(Role.role_key)
    ))
    permissions = list(db.scalars(
        select(Permission.permission_key).join(RolePermission).join(Role).join(EmployeeRole).where(
            EmployeeRole.employee_id == session.employee_id,
            Role.active.is_(True), Permission.active.is_(True),
        ).distinct().order_by(Permission.permission_key)
    ))
    return session.employee, roles, permissions
