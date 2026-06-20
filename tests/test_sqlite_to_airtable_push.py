import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from airtable.scripts.push_sqlite_to_airtable import (
    CONFIRM_TEXT,
    TABLE_SPECS,
    PushPlan,
    _airtable_value,
    apply_plan,
    main,
    plan_push,
    validate_contract,
)
from app.core.database import Base
from app.models import CashShift, DiningTable, Employee, ServiceZone, Ticket

ROOT = Path(__file__).resolve().parents[1]


def _json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


def _field_map():
    return _json("airtable/schema/field_map.v1.json")


def _schema():
    return _json("airtable/schema/kanpai_airtable_schema.v1.json")


def _engine():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _remote():
    tables = {spec.airtable_table for spec in TABLE_SPECS}
    tables.update(
        link.target_table for spec in TABLE_SPECS for link in spec.links.values()
    )
    return {table: [] for table in tables}


def _seed_shift(session: Session) -> CashShift:
    employee = Employee(
        employee_code="EMP-1",
        full_name="Operador Uno",
        pos_alias="Operador",
        pin_hash="test",
        active=True,
    )
    session.add(employee)
    session.flush()
    shift = CashShift(
        folio="COR-1",
        status="Cerrado",
        opened_by_employee_id=employee.id,
        closed_by_employee_id=employee.id,
        opening_cash_cents=10000,
        declared_cash_cents=10000,
        expected_cash_cents=10000,
        cash_difference_cents=0,
    )
    session.add(shift)
    session.flush()
    return shift


def test_contract_matches_schema_and_models():
    assert validate_contract(_field_map(), _schema()) == []


def test_datetime_serialization_matches_airtable_utc_milliseconds():
    assert _airtable_value(datetime(2026, 6, 20, 12, 34, 56, 715179)) == (
        "2026-06-20T18:34:56.715Z"
    )
    offset = timezone(timedelta(hours=-6))
    assert _airtable_value(datetime(2026, 6, 20, 6, 34, 56, 715999, tzinfo=offset)) == (
        "2026-06-20T12:34:56.715Z"
    )


def test_dry_run_plans_without_writing_sqlite():
    engine = _engine()
    with Session(engine) as session, session.begin():
        shift = _seed_shift(session)
        shift_id = shift.id
    remote = _remote()
    remote["Empleados"] = [
        {"id": "rec-employee", "fields": {"codigo_empleado": "EMP-1"}}
    ]

    with Session(engine) as session:
        plan = plan_push(session, remote, _field_map())
        assert plan.summary("CortesCaja")["create"] == 1
        assert plan.records["CortesCaja"][0].fields["id_sqlite"] == shift_id
        assert plan.records["CortesCaja"][0].fields["abierto_por"] == ["rec-employee"]
        assert session.scalar(select(func.count()).select_from(CashShift)) == 1


def test_comparison_is_idempotent():
    engine = _engine()
    with Session(engine) as session, session.begin():
        _seed_shift(session)
    remote = _remote()
    remote["Empleados"] = [
        {"id": "rec-employee", "fields": {"codigo_empleado": "EMP-1"}}
    ]
    with Session(engine) as session:
        first = plan_push(session, remote, _field_map())
        desired = first.records["CortesCaja"][0].fields
        remote["CortesCaja"] = [{"id": "rec-shift", "fields": desired}]
        second = plan_push(session, remote, _field_map())
    assert second.summary("CortesCaja") == {
        "create": 0,
        "update": 0,
        "unchanged": 1,
        "skipped": 0,
        "error": 0,
    }


def test_dependency_order_is_explicit():
    assert [spec.airtable_table for spec in TABLE_SPECS] == [
        "CortesCaja",
        "Tickets",
        "LineasTicket",
        "Pagos",
        "TrabajosImpresion",
        "HistorialSMS",
        "EventosAuditoria",
    ]


def test_remote_only_records_are_not_deleted_or_planned():
    engine = _engine()
    remote = _remote()
    remote["CortesCaja"] = [
        {"id": "rec-orphan", "fields": {"id_sqlite": 999, "folio": "OLD"}}
    ]
    with Session(engine) as session:
        plan = plan_push(session, remote, _field_map())
    assert plan.records["CortesCaja"] == []
    assert plan.remote_counts["CortesCaja"] == 1
    assert "delete" not in {item.action for rows in plan.records.values() for item in rows}


def test_execute_requires_exact_confirmation():
    with pytest.raises(SystemExit, match=CONFIRM_TEXT):
        main(["--execute", "--confirm", "WRONG"])


def test_links_resolve_by_natural_key_and_id_sqlite():
    engine = _engine()
    with Session(engine) as session, session.begin():
        shift = _seed_shift(session)
        employee_id = shift.opened_by_employee_id
        zone = ServiceZone(zone_key="SALON", name="Salón", active=True)
        session.add(zone)
        session.flush()
        table = DiningTable(
            table_code="M01",
            display_name="Mesa 1",
            zone_id=zone.id,
            status_cache="Libre",
            active=True,
        )
        session.add(table)
        session.flush()
        ticket = Ticket(
            folio="T-1",
            cash_shift_id=shift.id,
            table_id=table.id,
            opened_by_employee_id=employee_id,
            guest_count=1,
            status="Abierto",
            payment_status="Sin pagar",
        )
        session.add(ticket)
        session.flush()
        shift_id = shift.id
        ticket_id = ticket.id

    remote = _remote()
    remote["Empleados"] = [
        {"id": "rec-employee", "fields": {"codigo_empleado": "EMP-1"}}
    ]
    remote["Mesas"] = [{"id": "rec-table", "fields": {"codigo_mesa": "M01"}}]
    remote["CortesCaja"] = [
        {"id": "rec-shift", "fields": {"id_sqlite": shift_id}}
    ]
    with Session(engine) as session:
        plan = plan_push(session, remote, _field_map())
    fields = next(item.fields for item in plan.records["Tickets"] if item.key == str(ticket_id))
    assert fields["corte_caja"] == ["rec-shift"]
    assert fields["mesa"] == ["rec-table"]
    assert fields["abierto_por"] == ["rec-employee"]


def test_apply_plan_calls_only_create_and_update_apis():
    class Client:
        def __init__(self):
            self.calls = []

        def create_records(self, table, records):
            self.calls.append(("create", table, records))
            return []

        def update_records(self, table, records):
            self.calls.append(("update", table, records))
            return []

    client = Client()
    plan = PushPlan(
        {spec.airtable_table: [] for spec in TABLE_SPECS},
        [],
        {spec.airtable_table: 0 for spec in TABLE_SPECS},
        {spec.airtable_table: 1 for spec in TABLE_SPECS},
    )
    apply_plan(client, plan)
    assert {call[0] for call in client.calls} == {"create", "update"}
    assert not hasattr(client, "delete_records")
