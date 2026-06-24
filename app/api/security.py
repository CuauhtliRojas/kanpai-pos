"""Dependencias de seguridad para fronteras locales de API."""

from dataclasses import dataclass
import hmac
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models import Employee
from app.services.auth_service import get_session_identity
from app.services.exceptions import BusinessError

session_header = APIKeyHeader(
    name="X-Kanpai-Session",
    scheme_name="KanpaiSession",
    description="Token de sesión local obtenido mediante login por PIN.",
    auto_error=False,
)
worker_key_header = APIKeyHeader(
    name="X-Kanpai-Worker-Key",
    scheme_name="KanpaiWorkerKey",
    description="Clave local compartida exclusivamente con el worker de impresión.",
    auto_error=False,
)


@dataclass(frozen=True)
class SessionIdentity:
    employee: Employee
    roles: frozenset[str]
    permissions: frozenset[str]


def require_session(
    token: Annotated[str | None, Security(session_header)],
    db: Session = Depends(get_db),
) -> SessionIdentity:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta X-Kanpai-Session.",
        )
    try:
        employee, roles, permissions = get_session_identity(db, token)
        return SessionIdentity(employee, frozenset(roles), frozenset(permissions))
    except BusinessError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión no es válida o ya no está activa.",
        ) from None


def require_session_permission(permission_key: str) -> Callable:
    def dependency(
        identity: SessionIdentity = Depends(require_session),
    ) -> SessionIdentity:
        if permission_key not in identity.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"La sesión no tiene el permiso {permission_key}.",
            )
        return identity

    return dependency


def require_support_permission(
    identity: SessionIdentity = Depends(require_session),
) -> SessionIdentity:
    if "SUPPORT_ACCESS" not in identity.permissions and "ADMIN" not in identity.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La sesión no tiene acceso de soporte.",
        )
    return identity


def require_admin_read_permission(
    identity: SessionIdentity = Depends(require_session),
) -> SessionIdentity:
    if "ADMIN_READ" not in identity.permissions and "ADMIN" not in identity.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La sesión no tiene acceso administrativo.",
        )
    return identity


def require_reprint_or_support_permission(
    identity: SessionIdentity = Depends(require_session),
) -> SessionIdentity:
    if (
        "REPRINT" not in identity.permissions
        and "SUPPORT_ACCESS" not in identity.permissions
        and "ADMIN" not in identity.roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La sesión no tiene permiso de reimpresión.",
        )
    return identity


def require_worker_key(
    supplied_key: Annotated[str | None, Security(worker_key_header)],
) -> None:
    settings = get_settings()
    configured_key = settings.kanpai_worker_key
    if configured_key is None:
        if settings.app_env.lower() in {"local", "dev", "development", "test", "testing"}:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La autenticación del worker no está configurada.",
        )
    if supplied_key is None or not hmac.compare_digest(supplied_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Worker key inválida.",
        )
