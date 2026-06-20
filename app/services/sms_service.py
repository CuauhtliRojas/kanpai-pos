"""Cliente LabsMobile persistente, tolerante a fallos e inyectable en pruebas."""

import base64
import json
from datetime import datetime
from typing import Callable
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.constants import NotificationChannelKey, PermissionKey, SmsStatus, audit_event
from app.models import AuditEvent, NotificationChannel, SmsNotification, StockAlert
from app.services.permission_service import require_employee_permission

LABSMOBILE_URL = "https://api.labsmobile.com/json/send"
Transport = Callable[[str, dict, dict], tuple[int, str]]


def _default_transport(url: str, payload: dict, headers: dict) -> tuple[int, str]:
    """Ejecuta la solicitud HTTP con biblioteca estándar y timeout acotado."""
    request = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urlopen(request, timeout=10) as response:  # noqa: S310 - URL constante HTTPS
        return response.status, response.read().decode(errors="replace")


def send_sms(
    db: Session,
    *,
    employee_id: int | None,
    msisdn: str,
    message: str,
    stock_alert_id: int | None = None,
    require_permission: bool = True,
    transport: Transport | None = None,
) -> SmsNotification:
    """Persiste el intento antes de enviar y convierte cualquier fallo en historial."""
    if require_permission and employee_id is not None:
        require_employee_permission(db, employee_id, PermissionKey.SMS_SEND)
    existing = None
    if stock_alert_id is not None:
        existing = db.scalar(select(SmsNotification).where(SmsNotification.stock_alert_id == stock_alert_id))
    if existing is not None:
        return existing
    settings = get_settings()
    channel = db.scalar(select(NotificationChannel).where(NotificationChannel.channel_key == NotificationChannelKey.SMS))
    notification = SmsNotification(
        channel_id=channel.id if channel else None,
        stock_alert_id=stock_alert_id,
        employee_id=employee_id,
        msisdn=msisdn.strip(),
        message=message.strip(),
        status=SmsStatus.PENDING,
        test_mode=settings.labsmobile_test_mode,
    )
    db.add(notification)
    db.flush()
    if not settings.sms_enabled:
        notification.status = SmsStatus.SIMULATED
        notification.response_payload = json.dumps({"simulated": True, "reason": "SMS_ENABLED=false"})
        notification.sent_at = datetime.utcnow()
        db.flush()
        return notification
    try:
        if not settings.labsmobile_user or not settings.labsmobile_token:
            raise RuntimeError("Faltan credenciales LabsMobile.")
        payload: dict = {"message": notification.message, "recipient": [{"msisdn": notification.msisdn}]}
        if settings.labsmobile_test_mode:
            payload["test"] = 1
        basic = base64.b64encode(f"{settings.labsmobile_user}:{settings.labsmobile_token}".encode()).decode()
        code, body = (transport or _default_transport)(
            LABSMOBILE_URL, payload, {"Content-Type": "application/json", "Authorization": f"Basic {basic}"}
        )
        notification.response_payload = body[:4000]
        notification.status = SmsStatus.SENT if 200 <= code < 300 else SmsStatus.FAILED
        if notification.status == SmsStatus.FAILED:
            notification.error = f"LabsMobile HTTP {code}"
    except Exception as error:  # proveedor externo: nunca propagar a la venta
        notification.status = SmsStatus.FAILED
        notification.error = str(error)[:1000]
        db.add(AuditEvent(
            event_type=audit_event("SMS_FAILED"), entity_type="SmsNotification", entity_id=notification.id,
            actor_employee_id=employee_id, after_snapshot=json.dumps({"status": SmsStatus.FAILED, "error": notification.error}),
        ))
    notification.sent_at = datetime.utcnow()
    db.flush()
    return notification


def notify_stock_alert(db: Session, alert: StockAlert, employee_id: int) -> SmsNotification | None:
    """Crea exactamente un SMS por alerta de stock usando el destinatario configurado."""
    settings = get_settings()
    if not settings.labsmobile_default_msisdn:
        return None
    item = alert.inventory_item
    unit = item.base_unit.name
    message = (
        f"KANPAI: stock bajo en {item.name} ({item.item_code}). "
        f"Actual: {alert.current_quantity} {unit}. Minimo: {alert.threshold_quantity} {unit}. Revisar compra."
    )
    return send_sms(
        db, employee_id=employee_id, msisdn=settings.labsmobile_default_msisdn,
        message=message, stock_alert_id=alert.id, require_permission=False,
    )


def list_sms(db: Session) -> list[SmsNotification]:
    return list(db.scalars(select(SmsNotification).order_by(SmsNotification.id.desc())))
