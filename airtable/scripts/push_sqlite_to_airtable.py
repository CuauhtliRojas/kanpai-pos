"""Non-destructive SQLite -> Airtable operational mirror push."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

try:
    from sqlalchemy import create_engine, inspect, select
    from sqlalchemy.orm import Session
except ModuleNotFoundError as error:
    if error.name != "sqlalchemy":
        raise
    raise SystemExit(
        subprocess.run(
            ["uv", "run", "python", __file__, *sys.argv[1:]], check=False
        ).returncode
    ) from error

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for import_path in (ROOT, SCRIPT_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from airtable_records_client import (  # noqa: E402
    AirtableRecordsClient,
    AirtableRecordsError,
    _same_value,
)
from app.core.config import get_settings  # noqa: E402
from app.models import (  # noqa: E402
    AuditEvent,
    CashExpense,
    CashShift,
    DiningTable,
    Employee,
    NotificationChannel,
    Payment,
    PaymentMethod,
    Printer,
    PrintJob,
    Product,
    SmsNotification,
    Ticket,
    TicketLine,
)

CONFIRM_TEXT = "PUSH_SQLITE_TO_AIRTABLE"
DEFAULT_FIELD_MAP = Path("airtable/schema/field_map.v1.json")
DEFAULT_AIRTABLE_SCHEMA = Path("airtable/schema/kanpai_airtable_schema.v1.json")
DEFAULT_REPORT = Path("airtable/reports/sqlite_to_airtable_push_report.md")
SYNC_STATE = "Sincronizado"
PENDING_LINK_PREFIX = "pending:"
SQLITE_LOCAL_TIMEZONE = timezone(timedelta(hours=-6), name="America/Mexico_City")


@dataclass(frozen=True)
class LinkSpec:
    target_table: str
    target_model: type
    target_local_key: str
    target_remote_key: str
    required: bool = False


@dataclass(frozen=True)
class TableSpec:
    airtable_table: str
    model: type
    links: dict[str, LinkSpec] = field(default_factory=dict)


TABLE_SPECS = (
    TableSpec(
        "CortesCaja",
        CashShift,
        {
            "abierto_por": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado", True),
            "cerrado_por": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado"),
        },
    ),
    TableSpec(
        "Tickets",
        Ticket,
        {
            "corte_caja": LinkSpec("CortesCaja", CashShift, "id", "id_sqlite", True),
            "mesa": LinkSpec("Mesas", DiningTable, "table_code", "codigo_mesa", True),
            "abierto_por": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado", True),
        },
    ),
    TableSpec(
        "LineasTicket",
        TicketLine,
        {
            "ticket": LinkSpec("Tickets", Ticket, "id", "id_sqlite", True),
            "producto": LinkSpec("Productos", Product, "sku", "sku", True),
        },
    ),
    TableSpec(
        "Pagos",
        Payment,
        {
            "ticket": LinkSpec("Tickets", Ticket, "id", "id_sqlite", True),
            "corte_caja": LinkSpec("CortesCaja", CashShift, "id", "id_sqlite", True),
            "metodo_pago": LinkSpec("MetodosPago", PaymentMethod, "method_key", "clave_metodo", True),
            "cajero": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado", True),
        },
    ),
    TableSpec(
        "GastosCaja",
        CashExpense,
        {
            "corte_caja": LinkSpec("CortesCaja", CashShift, "id", "id_sqlite", True),
            "registrado_por": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado", True),
            "autorizado_por": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado"),
            "metodo_pago": LinkSpec("MetodosPago", PaymentMethod, "method_key", "clave_metodo"),
        },
    ),
    TableSpec(
        "TrabajosImpresion",
        PrintJob,
        {
            "impresora": LinkSpec("Impresoras", Printer, "printer_key", "clave_impresora", True),
            "ticket": LinkSpec("Tickets", Ticket, "id", "id_sqlite"),
        },
    ),
    TableSpec(
        "HistorialSMS",
        SmsNotification,
        {
            "canal": LinkSpec("CanalesNotificacion", NotificationChannel, "channel_key", "clave_canal"),
            "empleado": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado"),
        },
    ),
    TableSpec(
        "EventosAuditoria",
        AuditEvent,
        {
            "actor_empleado": LinkSpec("Empleados", Employee, "employee_code", "codigo_empleado"),
            "corte_caja": LinkSpec("CortesCaja", CashShift, "id", "id_sqlite"),
            "ticket": LinkSpec("Tickets", Ticket, "id", "id_sqlite"),
        },
    ),
)
SPEC_BY_TABLE = {spec.airtable_table: spec for spec in TABLE_SPECS}
OUT_OF_SCOPE_TABLES = {
    "LotesComanda / OrdenesEstacion": "Fuera de alcance Airtable v1 por decisión arquitectónica.",
    "MovimientosInventario detallados": "Fuera de alcance Airtable v1 por decisión arquitectónica.",
}


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    message: str
    table: str = ""
    key: str = ""


@dataclass(frozen=True)
class PlannedRecord:
    action: str
    key: str
    fields: dict[str, Any]
    record_id: str = ""
    changed_fields: tuple[str, ...] = ()


@dataclass
class PushPlan:
    records: dict[str, list[PlannedRecord]]
    issues: list[Issue]
    local_counts: dict[str, int]
    remote_counts: dict[str, int]

    def summary(self, table: str) -> dict[str, int]:
        result = {name: 0 for name in ("create", "update", "unchanged", "skipped", "error")}
        for item in self.records.get(table, []):
            result[item.action] += 1
        result["skipped"] = max(0, self.local_counts.get(table, 0) - len(self.records.get(table, [])))
        result["error"] = sum(
            issue.level == "error" and issue.table == table for issue in self.issues
        )
        return result


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _identity(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, Decimal)):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip().casefold()


def _airtable_value(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=SQLITE_LOCAL_TIMEZONE)
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return f"{value.isoformat(timespec='milliseconds')}Z"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def validate_contract(field_map: dict[str, Any], schema: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    schema_tables = {
        table["name"]: {item["name"]: item for item in table["fields"]}
        for table in schema.get("tables", [])
    }
    for spec in TABLE_SPECS:
        mapping = field_map.get("tables", {}).get(spec.airtable_table)
        if not mapping or mapping.get("direction") != "push_to_airtable_readonly":
            issues.append(Issue("error", "missing_push_mapping", "Falta mapping push readonly.", spec.airtable_table))
            continue
        if mapping.get("sqlite_table") != spec.model.__tablename__:
            issues.append(Issue("error", "sqlite_table_mismatch", "La tabla SQLite no coincide con el ORM.", spec.airtable_table))
        if mapping.get("primary_key") != "id_sqlite" or mapping.get("fields", {}).get("id_sqlite") != "id":
            issues.append(Issue("error", "unsafe_idempotency_key", "El push requiere id_sqlite -> id.", spec.airtable_table))
        model_fields = {column.key for column in inspect(spec.model).columns}
        remote_fields = schema_tables.get(spec.airtable_table)
        if remote_fields is None:
            issues.append(Issue("error", "missing_airtable_table", "La tabla no existe en schema v1.", spec.airtable_table))
            continue
        for remote, local in mapping.get("fields", {}).items():
            if remote not in remote_fields:
                issues.append(Issue("error", "missing_airtable_field", remote, spec.airtable_table))
            if local not in model_fields:
                issues.append(Issue("error", "missing_sqlite_field", local, spec.airtable_table))
        for remote, link in spec.links.items():
            field_schema = remote_fields.get(remote, {})
            if field_schema.get("type") != "link" or field_schema.get("target") != link.target_table:
                issues.append(Issue("error", "link_contract_mismatch", remote, spec.airtable_table))
    return issues


def required_remote_fields(field_map: dict[str, Any]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for spec in TABLE_SPECS:
        result.setdefault(spec.airtable_table, set()).update(
            field_map["tables"][spec.airtable_table]["fields"]
        )
        for link in spec.links.values():
            result.setdefault(link.target_table, set()).add(link.target_remote_key)
    return result


def fetch_remote_records(
    client: AirtableRecordsClient, field_map: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    return {
        table: client.list_records(table, fields=sorted(fields))
        for table, fields in required_remote_fields(field_map).items()
    }


def build_remote_indexes(
    remote: dict[str, list[dict[str, Any]]], field_map: dict[str, Any]
) -> tuple[dict[str, dict[str, dict[str, Any]]], list[Issue]]:
    key_fields = {
        spec.airtable_table: field_map["tables"][spec.airtable_table]["primary_key"]
        for spec in TABLE_SPECS
    }
    for spec in TABLE_SPECS:
        for link in spec.links.values():
            key_fields[link.target_table] = link.target_remote_key
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    issues: list[Issue] = []
    for table, key_field in key_fields.items():
        index: dict[str, dict[str, Any]] = {}
        for record in remote.get(table, []):
            value = record.get("fields", {}).get(key_field)
            if value in (None, ""):
                continue
            key = _identity(value)
            if key in index:
                issues.append(Issue("error", "duplicate_remote_key", f"{key_field}={value!r}", table, key))
            else:
                index[key] = record
        indexes[table] = index
    return indexes, issues


def _resolve_link(
    session: Session,
    local_fk: Any,
    link: LinkSpec,
    indexes: dict[str, dict[str, dict[str, Any]]],
    pending: dict[str, set[str]],
) -> tuple[list[str], str | None]:
    if local_fk is None:
        return [], None
    target = session.get(link.target_model, local_fk)
    if target is None:
        return [], f"FK local inexistente: {link.target_model.__tablename__}.{local_fk}"
    target_key = _identity(getattr(target, link.target_local_key))
    remote = indexes.get(link.target_table, {}).get(target_key)
    if remote:
        return [remote["id"]], None
    if target_key in pending.get(link.target_table, set()):
        return [f"{PENDING_LINK_PREFIX}{link.target_table}:{target_key}"], None
    return [], f"Link remoto no resuelto: {link.target_table}.{link.target_remote_key}={target_key}"


def _record_fields(
    session: Session,
    spec: TableSpec,
    obj: Any,
    field_map: dict[str, Any],
    indexes: dict[str, dict[str, dict[str, Any]]],
    pending: dict[str, set[str]],
) -> tuple[dict[str, Any], list[str], list[str]]:
    fields: dict[str, Any] = {}
    errors: list[str] = []
    warnings: list[str] = []
    for remote_field, local_attr in field_map["tables"][spec.airtable_table]["fields"].items():
        value = getattr(obj, local_attr)
        if remote_field in spec.links:
            value, error = _resolve_link(session, value, spec.links[remote_field], indexes, pending)
            if error and spec.links[remote_field].required:
                errors.append(error)
            elif error:
                warnings.append(error)
                value = []
        else:
            value = _airtable_value(value)
        fields[remote_field] = value
    fields["estado_sync"] = SYNC_STATE
    return fields, errors, warnings


def plan_push(
    session: Session,
    remote: dict[str, list[dict[str, Any]]],
    field_map: dict[str, Any],
    *,
    allow_pending_links: bool = True,
) -> PushPlan:
    indexes, issues = build_remote_indexes(remote, field_map)
    local_rows = {
        spec.airtable_table: session.scalars(select(spec.model).order_by(spec.model.id)).all()
        for spec in TABLE_SPECS
    }
    pending = {
        spec.airtable_table: {_identity(obj.id) for obj in rows}
        for spec, rows in ((item, local_rows[item.airtable_table]) for item in TABLE_SPECS)
    } if allow_pending_links else {}
    planned: dict[str, list[PlannedRecord]] = {spec.airtable_table: [] for spec in TABLE_SPECS}
    for spec in TABLE_SPECS:
        linked_fields = set(spec.links)
        for obj in local_rows[spec.airtable_table]:
            key = _identity(obj.id)
            fields, link_errors, link_warnings = _record_fields(
                session, spec, obj, field_map, indexes, pending
            )
            issues.extend(
                Issue("warning", "unresolved_optional_link", message, spec.airtable_table, key)
                for message in link_warnings
            )
            if link_errors:
                issues.append(Issue("error", "unresolved_required_link", "; ".join(link_errors), spec.airtable_table, key))
                continue
            remote_record = indexes.get(spec.airtable_table, {}).get(key)
            if remote_record is None:
                planned[spec.airtable_table].append(PlannedRecord("create", key, fields))
                continue
            remote_fields = remote_record.get("fields", {})
            changed = tuple(
                field_name
                for field_name, value in fields.items()
                if not _same_value(remote_fields.get(field_name), value, linked=field_name in linked_fields)
            )
            action = "update" if changed else "unchanged"
            planned[spec.airtable_table].append(
                PlannedRecord(action, key, fields, remote_record["id"], changed)
            )
    return PushPlan(
        planned,
        issues,
        {table: len(rows) for table, rows in local_rows.items()},
        {table: len(remote.get(table, [])) for table in planned},
    )


def apply_plan(client: AirtableRecordsClient, plan: PushPlan) -> None:
    """Apply only creates/updates; this API deliberately has no delete path."""
    for spec in TABLE_SPECS:
        items = plan.records[spec.airtable_table]
        payloads = [value for item in items for value in item.fields.values()]
        strings = [
            nested
            for value in payloads
            for nested in (value if isinstance(value, list) else [value])
        ]
        if any(isinstance(value, str) and value.startswith(PENDING_LINK_PREFIX) for value in strings):
            raise AirtableRecordsError("El plan contiene links pendientes; debe replanearse por dependencias.")
        client.create_records(
            spec.airtable_table,
            [item.fields for item in items if item.action == "create"],
        )
        client.update_records(
            spec.airtable_table,
            [
                {"id": item.record_id, "fields": {name: item.fields[name] for name in item.changed_fields}}
                for item in items
                if item.action == "update"
            ],
        )


def execute_sequential(
    client: AirtableRecordsClient,
    session: Session,
    remote: dict[str, list[dict[str, Any]]],
    field_map: dict[str, Any],
) -> None:
    """Replan each dependency level so newly created parent record IDs resolve."""
    for spec in TABLE_SPECS:
        current = plan_push(session, remote, field_map, allow_pending_links=False)
        table_issues = [issue for issue in current.issues if issue.table == spec.airtable_table]
        if table_issues:
            raise AirtableRecordsError(table_issues[0].message)
        items = current.records[spec.airtable_table]
        created = client.create_records(
            spec.airtable_table,
            [item.fields for item in items if item.action == "create"],
        )
        updated = client.update_records(
            spec.airtable_table,
            [
                {"id": item.record_id, "fields": {name: item.fields[name] for name in item.changed_fields}}
                for item in items
                if item.action == "update"
            ],
        )
        by_id = {record["id"]: record for record in remote.get(spec.airtable_table, [])}
        by_id.update({record["id"]: record for record in (*created, *updated)})
        remote[spec.airtable_table] = list(by_id.values())


def render_report(plan: PushPlan, *, mode: str, executed: bool) -> str:
    lines = [
        "# SQLite -> Airtable push report",
        "",
        f"Modo: {mode}",
        f"Escrituras Airtable: {'sí' if executed else 'no'}",
        "Política: SQLite es fuente operativa; upsert idempotente por id_sqlite; sin deletes.",
        "",
        "## Resumen por tabla",
        "",
        "| SQLite | Airtable | Locales | Remotos | Create | Update | Unchanged | Skipped | Error |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for spec in TABLE_SPECS:
        summary = plan.summary(spec.airtable_table)
        lines.append(
            f"| `{spec.model.__tablename__}` | {spec.airtable_table} | {plan.local_counts.get(spec.airtable_table, 0)} | "
            f"{plan.remote_counts.get(spec.airtable_table, 0)} | {summary['create']} | {summary['update']} | "
            f"{summary['unchanged']} | {summary['skipped']} | {summary['error']} |"
        )
    lines.extend(["", "## Fuera de alcance Airtable v1", ""])
    lines.extend(f"- {table}: {reason}" for table, reason in OUT_OF_SCOPE_TABLES.items())
    lines.extend(["", "## Warnings y errores", ""])
    if plan.issues:
        for issue in plan.issues:
            location = ".".join(part for part in (issue.table, issue.key) if part)
            lines.append(f"- {issue.level}/{issue.code}{f' [{location}]' if location else ''}: {issue.message}")
    else:
        lines.append("- Sin hallazgos.")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--database-url", default=get_settings().database_url)
    parser.add_argument("--field-map", type=Path, default=DEFAULT_FIELD_MAP)
    parser.add_argument("--airtable-schema", type=Path, default=DEFAULT_AIRTABLE_SCHEMA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def run_push(
    args: argparse.Namespace, *, client: AirtableRecordsClient | None = None
) -> PushPlan:
    mode = "execute" if args.execute else "dry-run"
    if args.execute and args.confirm != CONFIRM_TEXT:
        raise ValueError(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")
    field_map = _read_json(args.field_map)
    schema = _read_json(args.airtable_schema)
    contract_issues = validate_contract(field_map, schema)
    remote: dict[str, list[dict[str, Any]]] = {}
    plan = PushPlan({}, contract_issues, {}, {})
    executed = False
    try:
        if not contract_issues:
            records_client = client or AirtableRecordsClient.from_env()
            remote = fetch_remote_records(records_client, field_map)
            engine = create_engine(args.database_url)
            with Session(engine) as session:
                plan = plan_push(session, remote, field_map)
                if args.execute and not any(issue.level == "error" for issue in plan.issues):
                    execute_sequential(records_client, session, remote, field_map)
                    executed = True
    except (AirtableRecordsError, OSError, ValueError) as error:
        plan.issues.append(Issue("error", "push_failed", str(error)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(plan, mode=mode, executed=executed), encoding="utf-8")
    return plan


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.execute and args.confirm != CONFIRM_TEXT:
        raise SystemExit(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")
    plan = run_push(args)
    mode = "execute" if args.execute else "dry-run"
    print(f"MODE: {mode}")
    for spec in TABLE_SPECS:
        summary = plan.summary(spec.airtable_table)
        print(
            f"{spec.airtable_table}: creates={summary['create']} updates={summary['update']} "
            f"unchanged={summary['unchanged']} skipped={summary['skipped']} errors={summary['error']}"
        )
    print(f"Warnings: {sum(issue.level == 'warning' for issue in plan.issues)}")
    print(f"Errores: {sum(issue.level == 'error' for issue in plan.issues)}")
    print(f"Reporte: {args.report}")
    return 1 if any(issue.level == "error" for issue in plan.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
