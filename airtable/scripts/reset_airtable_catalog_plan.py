"""Build an Airtable catalog reset plan; never mutates Airtable by default."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from airtable_records_client import AirtableRecordsClient
from build_airtable_seed import DEFAULT_EXCEL, DEFAULT_FIXED, NATURAL_KEYS, build_seed

CONFIRMATION = "RESET_AIRTABLE_CATALOG_REAL_SEED"
DEFAULT_SCHEMA = Path("airtable/schema/kanpai_airtable_schema.v1.json")
DEFAULT_FIELD_MAP = Path("airtable/schema/field_map.v1.json")
DEFAULT_REPORT = Path("airtable/reports/airtable_catalog_reset_dry_run.md")
CATALOG_TABLES = (
    "CategoriasMenu", "EstacionesProduccion", "Impresoras", "InsumosInventario",
    "Productos", "AsignacionesProductoEstacion", "RecetasProducto", "Mesas", "Empleados",
)


def plan_records(seed_records: list[dict[str, Any]], remote_records: list[dict[str, Any]], key: str) -> dict[str, list[str]]:
    desired = {str(row[key]).strip(): row for row in seed_records}
    remote = {str(row.get("fields", {}).get(key, "")).strip(): row for row in remote_records}
    creates = sorted(set(desired) - set(remote))
    archives = sorted(value for value in set(remote) - set(desired) if value)
    updates = sorted(
        value for value in set(desired) & set(remote)
        if any(remote[value]["fields"].get(field) != expected for field, expected in desired[value].items())
    )
    unchanged = sorted(set(desired) & set(remote) - set(updates))
    return {"create": creates, "update": updates, "archive": archives, "delete": [], "unchanged": unchanged}


def build_plan(client: AirtableRecordsClient) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    schema = json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))
    field_map = json.loads(DEFAULT_FIELD_MAP.read_text(encoding="utf-8"))
    schema_tables = {table["name"] for table in schema["tables"]}
    mapped_tables = set(field_map["tables"])
    issues = [f"Contrato ausente para {table}" for table in CATALOG_TABLES if table not in schema_tables or table not in mapped_tables]
    seed = build_seed(DEFAULT_EXCEL, DEFAULT_FIXED)
    plan = {
        table: plan_records(seed.tables[table], client.list_records(table), NATURAL_KEYS[table])
        for table in CATALOG_TABLES
    }
    issues.extend(f"{issue.level}: {issue.code}: {issue.message}" for issue in seed.issues)
    return plan, issues


def render_report(plan: dict[str, dict[str, list[str]]], issues: list[str]) -> str:
    lines = ["# Airtable catalog reset dry-run", "", "No se proponen deletes; registros remotos fuera del seed se archivan.", ""]
    for table, actions in plan.items():
        lines.append(f"## {table}")
        lines.append("")
        for action in ("create", "update", "archive", "delete", "unchanged"):
            lines.append(f"- {action}: {len(actions[action])}")
        lines.append("")
    lines.extend(["## Issues", ""] + [f"- {issue}" for issue in issues] + [""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-id", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if args.execute:
        if args.confirm != CONFIRMATION:
            raise ValueError(f"Se requiere confirmación literal: {CONFIRMATION}")
        raise RuntimeError("La ejecución real no está habilitada en B3; revise y apruebe el dry-run.")
    plan, issues = build_plan(AirtableRecordsClient(args.app_id, args.token))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(plan, issues), encoding="utf-8")
    print(f"Dry-run: {args.report}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
