import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.constants import StockAlertStatus, StockStatus, audit_event
from app.models import AuditEvent, StockAlert


def evaluate_stock_alert(
    db: Session, inventory_item_id: int, employee_id: int
) -> StockAlert | None:
    """Abre, actualiza o resuelve la alerta local del stock calculado.

    Solo existe una alerta ``OPEN`` por insumo. Una recuperación estrictamente
    superior al mínimo la cambia a ``RESOLVED`` y conserva su historial.
    """
    from app.services.inventory_service import get_current_stock

    stock = get_current_stock(db, inventory_item_id)
    active_alert = (
        db.execute(
            select(StockAlert).where(
                StockAlert.inventory_item_id == inventory_item_id,
                StockAlert.status == StockAlertStatus.OPEN,
            )
        )
        .scalars()
        .first()
    )
    current = Decimal(stock["current_stock"])
    threshold = Decimal(stock["stock_minimum"])

    if stock["stock_status"] in {StockStatus.LOW, StockStatus.OUT}:
        message = (
            f"{stock['name']}: stock {current} {stock['base_unit_name']}; "
            f"mínimo {threshold} {stock['base_unit_name']}."
        )
        if active_alert is not None:
            active_alert.alert_type = stock["stock_status"]
            active_alert.current_quantity = current
            active_alert.threshold_quantity = threshold
            active_alert.message = message
            db.flush()
            return active_alert

        alert = StockAlert(
            inventory_item_id=inventory_item_id,
            alert_type=stock["stock_status"],
            status=StockAlertStatus.OPEN,
            threshold_quantity=threshold,
            current_quantity=current,
            message=message,
        )
        db.add(alert)
        db.flush()
        db.add(
            AuditEvent(
                event_type=audit_event("STOCK_ALERT_OPENED"),
                entity_type="StockAlert",
                entity_id=alert.id,
                actor_employee_id=employee_id,
                after_snapshot=json.dumps(
                    {
                        "inventory_item_id": inventory_item_id,
                        "alert_type": alert.alert_type,
                        "current_quantity": str(current),
                        "threshold_quantity": str(threshold),
                    },
                    ensure_ascii=False,
                ),
            )
        )
        db.flush()
        from app.services.sms_service import notify_stock_alert

        notify_stock_alert(db, alert, employee_id)
        return alert

    if active_alert is not None:
        active_alert.status = StockAlertStatus.RESOLVED
        active_alert.resolved_at = datetime.utcnow()
        active_alert.current_quantity = current
        active_alert.message = (
            f"Stock recuperado a {current} {stock['base_unit_name']}."
        )
        db.flush()
        db.add(
            AuditEvent(
                event_type=audit_event("STOCK_ALERT_RESOLVED"),
                entity_type="StockAlert",
                entity_id=active_alert.id,
                actor_employee_id=employee_id,
                before_snapshot=json.dumps({"status": StockAlertStatus.OPEN}),
                after_snapshot=json.dumps(
                    {
                        "status": StockAlertStatus.RESOLVED,
                        "current_quantity": str(current),
                    }
                ),
            )
        )
        db.flush()
        return active_alert
    return None


def list_active_stock_alerts(db: Session) -> list[StockAlert]:
    """Lista alertas locales abiertas, de la más antigua a la más reciente."""
    return list(
        db.execute(
            select(StockAlert)
            .where(StockAlert.status == StockAlertStatus.OPEN)
            .order_by(StockAlert.opened_at, StockAlert.id)
        ).scalars()
    )
