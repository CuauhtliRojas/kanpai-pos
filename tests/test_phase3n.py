import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.domain.constants import SmsStatus
from app.main import app
from app.models import (
    AuditEvent, CashShift, CommandBatch, DiningTable, Employee, EmployeeSession,
    InventoryMovement, Payment, PaymentMethod, PrintJob, Product, ProductVariantGroup,
    SmsNotification, StationOrder, StationOrderLine, StockAlert, TableStatusEvent,
    Ticket, TicketLine, TicketLineVariantSelection, TicketSplit, TicketSplitLine,
)
from app.services.cash_shift_service import open_cash_shift
from app.services.order_service import send_round
from app.services.payment_service import start_payment
from app.services.product_service import add_product_to_ticket
from app.services.reporting_service import get_sales_by_product
from app.services.preflight_service import run_local_backend_preflight
from app.services.sms_service import send_sms
from app.services.stock_alert_service import evaluate_stock_alert
from app.services.ticket_service import open_ticket_for_table


def _clean(db) -> None:
    for model in (
        SmsNotification, EmployeeSession, TicketSplitLine, TicketLineVariantSelection,
        PrintJob, StationOrderLine, StationOrder, CommandBatch, AuditEvent,
        TableStatusEvent, Payment, TicketSplit, InventoryMovement, StockAlert,
        TicketLine, Ticket, CashShift,
    ):
        db.execute(delete(model))
    db.execute(DiningTable.__table__.update().values(status_cache="Libre"))
    db.commit()


@pytest.fixture(autouse=True)
def phase3n_data():
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        _clean(db)
    yield
    with SessionLocal() as db:
        _clean(db)


def _context(db, sku="DEV-CHELA", quantity=1):
    employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
    table = db.scalar(select(DiningTable).where(DiningTable.active.is_(True)).order_by(DiningTable.id))
    product = db.scalar(select(Product).where(Product.sku == sku))
    shift = open_cash_shift(db, employee.id, 0)
    ticket = open_ticket_for_table(db, table.id, employee.id)
    return employee, shift, ticket, product


def test_pin_login_me_logout_and_hash_not_plaintext():
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login-pin",
        json={"employee_code": "EMP-0001", "pin": get_settings().kanpai_admin_pin},
    )
    assert login.status_code == 200
    token = login.json()["session_token"]
    me = client.get("/api/v1/auth/me", headers={"X-Kanpai-Session": token})
    assert me.status_code == 200
    assert "ADMIN" in me.json()["roles"]
    assert "SMS_SEND" in me.json()["permissions"]
    logout = client.post("/api/v1/auth/logout", json={"session_token": token})
    assert logout.json()["status"] == "Cerrada"
    assert client.get("/api/v1/auth/me", headers={"X-Kanpai-Session": token}).status_code == 401
    with SessionLocal() as db:
        employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
        assert employee.pin_hash != "1234"
        assert employee.pin_hash.startswith("pbkdf2_sha256$")


def test_pin_login_rejects_wrong_pin():
    response = TestClient(app).post("/api/v1/auth/login-pin", json={"employee_code": "EMP-0001", "pin": "9999"})
    assert response.status_code == 401


def test_variant_validation_creation_price_command_and_audit():
    with SessionLocal() as db:
        employee, _, ticket, product = _context(db, "DEV-YAKITORI-ORDEN-3")
        group = db.scalar(select(ProductVariantGroup).where(ProductVariantGroup.product_id == product.id))
        options = group.options
        with pytest.raises(Exception, match="requiere entre 3 y 3"):
            add_product_to_ticket(db, ticket.id, product.id, employee.id, 1, variant_selections=[{"variant_group_id": group.id, "variant_option_id": options[0].id, "quantity": 2}])
        with pytest.raises(Exception, match="requiere entre 3 y 3"):
            add_product_to_ticket(db, ticket.id, product.id, employee.id, 1, variant_selections=[{"variant_group_id": group.id, "variant_option_id": options[0].id, "quantity": 4}])
        options[0].price_delta_cents = 250
        selections = [{"variant_group_id": group.id, "variant_option_id": option.id, "quantity": 1} for option in options]
        line = add_product_to_ticket(db, ticket.id, product.id, employee.id, 1, "Orden yakitori", selections)[0]
        assert line.unit_price_cents == product.price_cents + 250
        assert len(line.variant_selections) == 3
        batch = send_round(db, ticket.id, employee.id)
        job = db.scalar(select(PrintJob).where(PrintJob.command_batch_id == batch.id))
        assert all(name in job.content_snapshot for name in ("Pollo", "Pulpo", "Verduras"))
        event = db.scalar(select(AuditEvent).where(AuditEvent.entity_id == line.id, AuditEvent.entity_type == "TicketLine"))
        assert len(json.loads(event.after_snapshot)["variant_selections"]) == 3
        ticket.status = "Cobrado"
        db.flush()
        report_item = next(item for item in get_sales_by_product(db) if item["product_id"] == product.id)
        assert {item["name"] for item in report_item["variant_breakdown"]} == {"Pollo", "Pulpo", "Verduras"}


def test_equal_splits_payments_change_and_ticket_closure():
    client = TestClient(app)
    with SessionLocal() as db:
        employee, _, ticket, product = _context(db)
        add_product_to_ticket(db, ticket.id, product.id, employee.id, 2)
        send_round(db, ticket.id, employee.id)
        start_payment(db, ticket.id, employee.id)
        cash = db.scalar(select(PaymentMethod).where(PaymentMethod.method_key == "Efectivo"))
        db.commit()
        employee_id, ticket_id, cash_id = employee.id, ticket.id, cash.id
    created = client.post(f"/api/v1/pos/tickets/{ticket_id}/splits/equal", json={"employee_id": employee_id, "parts": 2})
    assert created.status_code == 201
    splits = created.json()
    first = client.post(f"/api/v1/pos/ticket-splits/{splits[0]['id']}/payments", json={"employee_id": employee_id, "payment_method_id": cash_id, "amount_cents": splits[0]["amount_cents"], "received_cents": splits[0]["amount_cents"] + 500})
    assert first.json()["change_cents"] == 500
    assert first.json()["ticket_closed"] is False
    second = client.post(f"/api/v1/pos/ticket-splits/{splits[1]['id']}/payments", json={"employee_id": employee_id, "payment_method_id": cash_id, "amount_cents": splits[1]["amount_cents"], "received_cents": splits[1]["amount_cents"]})
    assert second.json()["ticket_closed"] is True
    with SessionLocal() as db:
        assert db.get(Ticket, ticket_id).status == "Cobrado"
        assert db.scalar(select(AuditEvent).where(AuditEvent.event_type == "Pago de division registrado"))


def test_split_by_lines():
    client = TestClient(app)
    with SessionLocal() as db:
        employee, _, ticket, product = _context(db)
        first = add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)[0]
        second = add_product_to_ticket(db, ticket.id, product.id, employee.id, 1)[0]
        db.commit()
        ids = employee.id, ticket.id, first.id, second.id
    response = client.post(f"/api/v1/pos/tickets/{ids[1]}/splits/by-lines", json={"employee_id": ids[0], "name": "Persona 1", "ticket_line_ids": [ids[2], ids[3]]})
    assert response.status_code == 201
    assert {line["ticket_line_id"] for line in response.json()["lines"]} == {ids[2], ids[3]}


def test_sms_simulation_stock_dedup_and_provider_failure(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "sms_enabled", False)
    monkeypatch.setattr(settings, "labsmobile_default_msisdn", "527775453934")
    with SessionLocal() as db:
        employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
        direct = send_sms(db, employee_id=employee.id, msisdn="527775453934", message="KANPAI prueba SMS")
        assert direct.status == SmsStatus.SIMULATED
        item_id = db.scalar(select(StockAlert.inventory_item_id).limit(1))
        if item_id is None:
            from app.models import InventoryItem
            item_id = db.scalar(select(InventoryItem.id).order_by(InventoryItem.id))
        alert = evaluate_stock_alert(db, item_id, employee.id)
        evaluate_stock_alert(db, item_id, employee.id)
        assert db.scalar(select(SmsNotification).where(SmsNotification.stock_alert_id == alert.id)).status == SmsStatus.SIMULATED
        assert len(db.scalars(select(SmsNotification).where(SmsNotification.stock_alert_id == alert.id)).all()) == 1
        monkeypatch.setattr(settings, "sms_enabled", True)
        monkeypatch.setattr(settings, "labsmobile_user", "user")
        monkeypatch.setattr(settings, "labsmobile_token", "token")
        failed = send_sms(db, employee_id=employee.id, msisdn="527775453934", message="fallo", transport=lambda *_: (_ for _ in ()).throw(RuntimeError("red caída")))
        assert failed.status == SmsStatus.FAILED
        assert "red caída" in failed.error


def test_preflight_warns_when_labsmobile_credentials_are_missing(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "sms_enabled", True)
    monkeypatch.setattr(settings, "labsmobile_user", None)
    monkeypatch.setattr(settings, "labsmobile_token", None)
    monkeypatch.setattr(settings, "labsmobile_default_msisdn", None)
    with SessionLocal() as db:
        report = run_local_backend_preflight(db)
    warning = next(check for check in report["checks"] if check["key"] == "labsmobile_credentials")
    assert warning["status"] == "WARNING"


def test_worker_dry_run_marks_printed_and_failure_marks_failed():
    script = Path(__file__).parents[1] / "scripts" / "print_worker_windows.py"
    spec = importlib.util.spec_from_file_location("print_worker_windows", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []
    job = {"id": 9, "content_snapshot": "KANPAI"}

    def http_ok(url, payload, worker_key):
        calls.append((url, payload, worker_key))
        return {"job": job} if url.endswith("claim-next") else {}

    config = {"api_base_url": "http://local", "worker_id": "qa", "worker_key": "secret", "printers": {"CAJA": "Caja"}}
    assert module.process_once(config, dry_run=True, http_post=http_ok) == 1
    assert calls[-1][0].endswith("/9/printed")
    assert calls[-1][2] == "secret"
    calls.clear()

    def broken_printer(*_):
        raise RuntimeError("sin papel")

    module.process_once(config, http_post=http_ok, printer=broken_printer)
    assert calls[-1][0].endswith("/9/failed")
    assert "sin papel" in calls[-1][1]["error_message"]


def test_worker_example_config_exists():
    assert (Path(__file__).parents[1] / "scripts" / "print_worker_config.example.json").exists()
