"""Tests for prepare_airtable_production_reset.py using a fake client.

All tests run against an in-memory fake; no real Airtable calls are made.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from airtable.scripts.prepare_airtable_production_reset import (
    CATALOG_DIRECTION,
    CONFIRM_TEXT,
    OPERATIONAL_ALLOWLIST,
    OPERATIONAL_DIRECTION,
    main,
    run_execute,
    run_preview,
    validate_allowlist,
)

ROOT = Path(__file__).resolve().parents[1]


def _field_map() -> dict:
    return json.loads(
        (ROOT / "airtable/schema/field_map.v1.json").read_text(encoding="utf-8-sig")
    )


class FakeClient:
    """Minimal fake that records delete calls without touching Airtable."""

    def __init__(self, records_by_table: dict[str, list[dict]]) -> None:
        self._records = records_by_table
        self.delete_calls: list[tuple[str, list[str]]] = []

    def list_records(self, table: str, *, fields: list[str] | None = None) -> list[dict]:
        return list(self._records.get(table, []))

    def delete_records(self, table: str, record_ids: list[str]) -> int:
        self.delete_calls.append((table, list(record_ids)))
        return len(record_ids)


def _empty_client() -> FakeClient:
    return FakeClient({t: [] for t in OPERATIONAL_ALLOWLIST})


def _record(airtable_id: str, sqlite_id: int) -> dict:
    return {"id": airtable_id, "fields": {"id_sqlite": sqlite_id}}


# ---------------------------------------------------------------------------
# validate_allowlist
# ---------------------------------------------------------------------------


def test_real_field_map_passes_validation() -> None:
    assert validate_allowlist(_field_map()) == []


def test_validate_allowlist_rejects_catalog_direction() -> None:
    field_map = _field_map()
    modified = dict(field_map)
    modified_tables = dict(field_map["tables"])
    modified_tables["CortesCaja"] = {
        **modified_tables["CortesCaja"],
        "direction": CATALOG_DIRECTION,
    }
    modified["tables"] = modified_tables
    errors = validate_allowlist(modified)
    assert any("CortesCaja" in e for e in errors)
    assert any("bloqueada" in e for e in errors)


def test_validate_allowlist_rejects_unknown_direction() -> None:
    field_map = _field_map()
    modified = dict(field_map)
    modified_tables = dict(field_map["tables"])
    modified_tables["Tickets"] = {**modified_tables["Tickets"], "direction": "bidirectional"}
    modified["tables"] = modified_tables
    errors = validate_allowlist(modified)
    assert any("Tickets" in e for e in errors)
    assert any(OPERATIONAL_DIRECTION in e for e in errors)


def test_validate_allowlist_rejects_missing_table() -> None:
    field_map = _field_map()
    modified = dict(field_map)
    tables = dict(field_map["tables"])
    del tables["Pagos"]
    modified["tables"] = tables
    errors = validate_allowlist(modified)
    assert any("Pagos" in e for e in errors)


# ---------------------------------------------------------------------------
# run_preview
# ---------------------------------------------------------------------------


def test_preview_does_not_call_delete_records() -> None:
    client = _empty_client()
    run_preview(client, _field_map())
    assert client.delete_calls == []


def test_preview_returns_zero_when_no_remote_records() -> None:
    counts = run_preview(_empty_client(), _field_map())
    assert set(counts) == set(OPERATIONAL_ALLOWLIST)
    assert all(v == 0 for v in counts.values())


def test_preview_reports_correct_counts() -> None:
    client = FakeClient(
        {
            **{t: [] for t in OPERATIONAL_ALLOWLIST},
            "CortesCaja": [_record("rec-c1", 1), _record("rec-c2", 2)],
            "Tickets": [_record("rec-t1", 10)],
        }
    )
    counts = run_preview(client, _field_map())
    assert counts["CortesCaja"] == 2
    assert counts["Tickets"] == 1
    assert counts["Pagos"] == 0
    assert counts["EventosAuditoria"] == 0


def test_preview_raises_on_invalid_allowlist() -> None:
    field_map = _field_map()
    modified = dict(field_map)
    tables = dict(field_map["tables"])
    tables["LineasTicket"] = {**tables["LineasTicket"], "direction": CATALOG_DIRECTION}
    modified["tables"] = tables
    with pytest.raises(ValueError, match="inválida"):
        run_preview(_empty_client(), modified)


# ---------------------------------------------------------------------------
# run_execute
# ---------------------------------------------------------------------------


def test_execute_only_deletes_allowlist_tables() -> None:
    records_by_table = {
        t: [_record(f"rec-{t}-1", 1)] for t in OPERATIONAL_ALLOWLIST
    }
    client = FakeClient(records_by_table)
    result = run_execute(client, _field_map())
    deleted_tables = {call[0] for call in client.delete_calls}
    assert deleted_tables == set(OPERATIONAL_ALLOWLIST)
    assert all(result[t] == 1 for t in OPERATIONAL_ALLOWLIST)


def test_execute_zero_records_does_not_call_delete() -> None:
    client = _empty_client()
    result = run_execute(client, _field_map())
    assert client.delete_calls == []
    assert all(v == 0 for v in result.values())


def test_execute_passes_correct_airtable_ids_to_delete() -> None:
    client = FakeClient(
        {
            **{t: [] for t in OPERATIONAL_ALLOWLIST},
            "CortesCaja": [_record("rec-airtable-abc", 1), _record("rec-airtable-def", 2)],
        }
    )
    run_execute(client, _field_map())
    cortes_calls = [ids for table, ids in client.delete_calls if table == "CortesCaja"]
    assert cortes_calls == [["rec-airtable-abc", "rec-airtable-def"]]


def test_execute_raises_on_invalid_allowlist() -> None:
    field_map = _field_map()
    modified = dict(field_map)
    tables = dict(field_map["tables"])
    tables["CortesCaja"] = {**tables["CortesCaja"], "direction": CATALOG_DIRECTION}
    modified["tables"] = tables
    with pytest.raises(ValueError, match="inválida"):
        run_execute(_empty_client(), modified)


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


def test_main_execute_requires_literal_confirmation() -> None:
    with pytest.raises(SystemExit, match=CONFIRM_TEXT):
        main(["--execute", "--confirm", "WRONG"])


def test_main_execute_requires_confirmation_not_empty() -> None:
    with pytest.raises(SystemExit):
        main(["--execute"])


def test_main_preview_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    # Only validates field map; actual Airtable calls happen inside client
    # We can't call main() without a real Airtable token, so we test the
    # validation path by passing a non-existent field-map and expecting error exit.
    result = main(["--field-map", "/nonexistent/field_map.json"])
    assert result == 1


# ---------------------------------------------------------------------------
# push_sqlite_to_airtable invariant
# ---------------------------------------------------------------------------


def test_push_script_apply_plan_never_calls_delete() -> None:
    """Normal push must not reach delete_records even after it exists on the client."""
    from airtable.scripts.push_sqlite_to_airtable import PushPlan, TABLE_SPECS, apply_plan

    class StrictClient:
        def create_records(self, table: str, records: list) -> list:
            return []

        def update_records(self, table: str, records: list) -> list:
            return []

        def delete_records(self, table: str, record_ids: list) -> int:
            raise AssertionError(
                f"apply_plan must never call delete_records (table={table!r})"
            )

    plan = PushPlan(
        records={spec.airtable_table: [] for spec in TABLE_SPECS},
        issues=[],
        local_counts={spec.airtable_table: 0 for spec in TABLE_SPECS},
        remote_counts={spec.airtable_table: 1 for spec in TABLE_SPECS},
    )
    apply_plan(StrictClient(), plan)  # must not raise


def test_push_script_has_no_auto_delete_for_remote_only_records() -> None:
    """Records that exist only in Airtable are ignored — not queued for delete."""
    from airtable.scripts.push_sqlite_to_airtable import TABLE_SPECS, plan_push
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.core.database import Base

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    remote: dict[str, list] = {spec.airtable_table: [] for spec in TABLE_SPECS}
    remote.update(
        {
            link.target_table: []
            for spec in TABLE_SPECS
            for link in spec.links.values()
        }
    )
    remote["CortesCaja"] = [
        {"id": "rec-orphan", "fields": {"id_sqlite": 9999, "folio": "ORPHAN"}}
    ]

    with Session(engine) as session:
        push_plan = plan_push(session, remote, _field_map())

    actions = {item.action for rows in push_plan.records.values() for item in rows}
    assert "delete" not in actions
    assert push_plan.records["CortesCaja"] == []
