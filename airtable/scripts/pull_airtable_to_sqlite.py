"""Controlled, non-destructive Airtable -> SQLite catalog pull."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

try:
    from sqlalchemy import Boolean, Integer, Numeric, create_engine, inspect, select
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
)
from app.core.config import get_settings  # noqa: E402
from app.models import (  # noqa: E402
    BusinessSetting,
    DiningTable,
    Employee,
    EmployeeRole,
    InventoryItem,
    MenuCategory,
    NotificationChannel,
    PaymentMethod,
    Printer,
    Product,
    ProductRecipe,
    ProductStationAssignment,
    ProductionStation,
    Role,
    ServiceZone,
    Unit,
)

CONFIRM_TEXT = "PULL_AIRTABLE_TO_SQLITE"
DEFAULT_FIELD_MAP = Path("airtable/schema/field_map.v1.json")
DEFAULT_AIRTABLE_SCHEMA = Path("airtable/schema/kanpai_airtable_schema.v1.json")
DEFAULT_REPORT = Path("airtable/reports/airtable_to_sqlite_pull_report.md")
FORBIDDEN_FIELDS = {
    "id_sqlite",
    "estado_sync",
    "revision_remota",
    "actualizado_sqlite_en",
    "actualizado_airtable_en",
    "ultimo_pull_en",
    "ultimo_push_en",
    "error_sync",
}
UNSUPPORTED_TABLES = {"DestinatariosNotificacion": "No existe tabla SQLite destino."}


@dataclass(frozen=True)
class LinkSpec:
    target_table: str
    many: bool = False
    required: bool = False


@dataclass(frozen=True)
class TableSpec:
    airtable_table: str
    model: type
    key_attrs: tuple[str, ...]
    links: dict[str, LinkSpec] = field(default_factory=dict)


TABLE_SPECS = (
    TableSpec("Unidades", Unit, ("unit_key",)),
    TableSpec("ZonasServicio", ServiceZone, ("zone_key",)),
    TableSpec("MetodosPago", PaymentMethod, ("method_key",)),
    TableSpec("EstacionesProduccion", ProductionStation, ("station_key",)),
    TableSpec("CategoriasMenu", MenuCategory, ("name",)),
    TableSpec("Roles", Role, ("role_key",)),
    TableSpec(
        "Empleados",
        Employee,
        ("employee_code",),
        {"roles": LinkSpec("Roles", many=True)},
    ),
    TableSpec(
        "Mesas",
        DiningTable,
        ("table_code",),
        {"zona": LinkSpec("ZonasServicio", required=True)},
    ),
    TableSpec(
        "Impresoras",
        Printer,
        ("printer_key",),
        {"estacion": LinkSpec("EstacionesProduccion")},
    ),
    TableSpec(
        "InsumosInventario",
        InventoryItem,
        ("item_code",),
        {"unidad_base": LinkSpec("Unidades", required=True)},
    ),
    TableSpec(
        "Productos",
        Product,
        ("sku",),
        {"categoria": LinkSpec("CategoriasMenu")},
    ),
    TableSpec(
        "AsignacionesProductoEstacion",
        ProductStationAssignment,
        ("product_id", "station_id"),
        {
            "producto": LinkSpec("Productos", required=True),
            "estacion": LinkSpec("EstacionesProduccion", required=True),
        },
    ),
    TableSpec(
        "RecetasProducto",
        ProductRecipe,
        ("product_id", "inventory_item_id"),
        {
            "producto": LinkSpec("Productos", required=True),
            "insumo": LinkSpec("InsumosInventario", required=True),
        },
    ),
    TableSpec("CanalesNotificacion", NotificationChannel, ("channel_key",)),
    TableSpec("ConfiguracionNegocio", BusinessSetting, ("business_name",)),
)
SPEC_BY_TABLE = {spec.airtable_table: spec for spec in TABLE_SPECS}


@dataclass(frozen=True)
class Issue:
    level: str
    code: str
    message: str
    table: str = ""
    key: str = ""


class NonIntegralValue(ValueError):
    """Value cannot be represented by an existing SQLite INTEGER column."""


@dataclass
class PreparedRecord:
    record_id: str
    key: tuple[Any, ...]
    values: dict[str, Any]
    links: dict[str, tuple[str, ...]]

    @property
    def label(self) -> str:
        return " + ".join(str(value) for value in self.key)


@dataclass
class PlannedRecord:
    action: str
    prepared: PreparedRecord
    changed_fields: tuple[str, ...] = ()


@dataclass
class PullPlan:
    records: dict[str, list[PlannedRecord]]
    issues: list[Issue]
    remote_counts: dict[str, int]
    preflight: list[str]

    def summary(self, table: str) -> dict[str, int]:
        result = {name: 0 for name in ("create", "update", "unchanged", "skipped", "error")}
        for item in self.records.get(table, []):
            result[item.action] += 1
        result["skipped"] = max(
            0, self.remote_counts.get(table, 0) - len(self.records.get(table, []))
        )
        result["error"] += sum(
            issue.level == "error" and issue.table == table for issue in self.issues
        )
        return result


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _model_columns(spec: TableSpec) -> dict[str, Any]:
    return {column.key: column for column in inspect(spec.model).columns}


def validate_field_map(
    field_map: dict[str, Any], airtable_schema: dict[str, Any]
) -> list[Issue]:
    issues: list[Issue] = []
    remote_fields = {
        table["name"]: {item["name"] for item in table["fields"]}
        for table in airtable_schema.get("tables", [])
    }
    mapped_tables = field_map.get("tables")
    if not isinstance(mapped_tables, dict):
        return [Issue("error", "invalid_field_map", "field_map.tables debe ser un objeto.")]

    for spec in TABLE_SPECS:
        mapping = mapped_tables.get(spec.airtable_table)
        if not mapping or mapping.get("direction") != "pull_to_sqlite":
            issues.append(
                Issue("error", "missing_pull_mapping", "Falta mapping pull_to_sqlite.", spec.airtable_table)
            )
            continue
        if mapping.get("sqlite_table") != spec.model.__tablename__:
            issues.append(
                Issue("error", "sqlite_table_mismatch", "La tabla SQLite no coincide con el ORM.", spec.airtable_table)
            )
        fields = mapping.get("fields", {})
        forbidden = sorted(set(fields) & FORBIDDEN_FIELDS)
        if forbidden:
            issues.append(
                Issue("error", "technical_field_mapped", f"Campos técnicos mapeados: {', '.join(forbidden)}", spec.airtable_table)
            )
        missing_remote = sorted(set(fields) - remote_fields.get(spec.airtable_table, set()))
        if missing_remote:
            issues.append(
                Issue("error", "unknown_airtable_field", f"Campos no declarados en schema: {', '.join(missing_remote)}", spec.airtable_table)
            )
        columns = _model_columns(spec)
        special_attrs = {"roles"}
        unknown_attrs = sorted(
            attr for attr in fields.values() if attr not in columns and attr not in special_attrs
        )
        if unknown_attrs:
            issues.append(
                Issue("error", "unknown_sqlite_attribute", f"Atributos ORM inexistentes: {', '.join(unknown_attrs)}", spec.airtable_table)
            )
        for source_field in spec.links:
            if source_field not in fields:
                issues.append(
                    Issue("error", "unmapped_link", f"Link no incluido en field_map: {source_field}", spec.airtable_table)
                )
    return issues


def normalize_bool(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float, Decimal)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        folded = value.strip().casefold()
        if folded in {"true", "1", "si", "sí", "yes", "x", "checked"}:
            return True
        if folded in {"false", "0", "no", "unchecked"}:
            return False
    raise ValueError(f"booleano inválido: {value!r}")


def normalize_integer(value: Any, *, nullable: bool) -> int | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if nullable:
            return None
        raise ValueError("entero obligatorio vacío")
    if isinstance(value, bool):
        raise ValueError(f"entero inválido: {value!r}")
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"entero inválido: {value!r}") from error
    if not number.is_finite() or number != number.to_integral_value():
        raise NonIntegralValue(f"entero no integral: {value!r}")
    return int(number)


def normalize_decimal(value: Any, *, nullable: bool, scale: int) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if nullable:
            return None
        raise ValueError("decimal obligatorio vacío")
    if isinstance(value, bool):
        raise ValueError(f"decimal inválido: {value!r}")
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"decimal inválido: {value!r}") from error
    if not number.is_finite():
        raise ValueError(f"decimal inválido: {value!r}")
    quantum = Decimal(1).scaleb(-scale)
    normalized = number.quantize(quantum)
    if normalized != number:
        raise ValueError(f"decimal excede escala {scale}: {value!r}")
    return normalized


def normalize_value(value: Any, column: Any) -> Any:
    if isinstance(column.type, Boolean):
        return normalize_bool(value)
    if isinstance(column.type, Integer):
        return normalize_integer(value, nullable=column.nullable)
    if isinstance(column.type, Numeric):
        return normalize_decimal(
            value,
            nullable=column.nullable,
            scale=column.type.scale or 0,
        )
    if value is None:
        if column.nullable:
            return None
        raise ValueError("valor obligatorio vacío")
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            if column.nullable:
                return None
            raise ValueError("texto obligatorio vacío")
        return normalized
    return value


def _remote_primary_field(field_map: dict[str, Any], table: str) -> str:
    key = field_map["tables"][table]["primary_key"]
    if not isinstance(key, str):
        raise ValueError(f"{table} no puede ser destino de link con clave compuesta.")
    return key


def fetch_remote_records(
    client: AirtableRecordsClient, field_map: dict[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for spec in TABLE_SPECS:
        allowed = list(field_map["tables"][spec.airtable_table]["fields"])
        result[spec.airtable_table] = client.list_records(spec.airtable_table, fields=allowed)
    return result


def build_remote_indexes(
    remote: dict[str, list[dict[str, Any]]], field_map: dict[str, Any]
) -> tuple[dict[str, dict[str, str]], list[Issue]]:
    indexes: dict[str, dict[str, str]] = {}
    issues: list[Issue] = []
    for spec in TABLE_SPECS:
        primary = field_map["tables"][spec.airtable_table]["primary_key"]
        if not isinstance(primary, str):
            continue
        by_id: dict[str, str] = {}
        seen: dict[str, str] = {}
        for record in remote[spec.airtable_table]:
            value = record.get("fields", {}).get(primary)
            key = value.strip() if isinstance(value, str) else str(value).strip() if value is not None else ""
            if not key:
                issues.append(Issue("error", "missing_natural_key", f"Registro {record.get('id', '?')} sin {primary}.", spec.airtable_table))
                continue
            folded = key.casefold()
            if folded in seen:
                issues.append(Issue("error", "duplicate_remote_key", f"Clave duplicada {key!r}.", spec.airtable_table, key))
                continue
            seen[folded] = record["id"]
            by_id[record["id"]] = key
        indexes[spec.airtable_table] = by_id
    return indexes, issues


def _resolve_link(
    raw: Any,
    link: LinkSpec,
    remote_indexes: dict[str, dict[str, str]],
) -> tuple[str, ...]:
    if raw in (None, "", []):
        if link.required:
            raise ValueError("link obligatorio vacío")
        return ()
    if not isinstance(raw, list):
        raise ValueError(f"link inválido: {raw!r}")
    if not link.many and len(raw) != 1:
        raise ValueError(f"se esperaba un link y llegaron {len(raw)}")
    target_index = remote_indexes.get(link.target_table, {})
    missing = [record_id for record_id in raw if record_id not in target_index]
    if missing:
        raise ValueError(f"record IDs no resueltos en {link.target_table}: {', '.join(missing)}")
    return tuple(target_index[record_id] for record_id in raw)


def prepare_records(
    remote: dict[str, list[dict[str, Any]]],
    field_map: dict[str, Any],
    remote_indexes: dict[str, dict[str, str]],
) -> tuple[dict[str, list[PreparedRecord]], list[Issue]]:
    prepared: dict[str, list[PreparedRecord]] = {}
    issues: list[Issue] = []
    for spec in TABLE_SPECS:
        mapping = field_map["tables"][spec.airtable_table]
        columns = _model_columns(spec)
        table_records: list[PreparedRecord] = []
        seen: set[tuple[Any, ...]] = set()
        for remote_record in remote[spec.airtable_table]:
            source = remote_record.get("fields", {})
            values: dict[str, Any] = {}
            links: dict[str, tuple[str, ...]] = {}

            def key_hint() -> str:
                primary = mapping.get("primary_key")
                if isinstance(primary, str):
                    return str(source.get(primary, "")).strip()
                linked = [values[0] for values in links.values() if values]
                return " + ".join(linked)

            try:
                for source_field, target_attr in mapping["fields"].items():
                    if source_field in spec.links:
                        links[source_field] = _resolve_link(
                            source.get(source_field), spec.links[source_field], remote_indexes
                        )
                        continue
                    column = columns[target_attr]
                    if source_field not in source and not isinstance(column.type, Boolean):
                        continue
                    values[target_attr] = normalize_value(source.get(source_field), column)

                key_parts: list[Any] = []
                for key_attr in spec.key_attrs:
                    linked_field = next(
                        (name for name, attr in mapping["fields"].items() if attr == key_attr and name in spec.links),
                        None,
                    )
                    if linked_field:
                        linked_values = links[linked_field]
                        if len(linked_values) != 1:
                            raise ValueError(f"clave compuesta {linked_field} no resuelta")
                        key_parts.append(linked_values[0])
                    elif key_attr in values:
                        key_parts.append(values[key_attr])
                    else:
                        raise ValueError(f"falta clave natural {key_attr}")
                key = tuple(key_parts)
                comparable_key = tuple(
                    value.casefold() if isinstance(value, str) else value for value in key
                )
                if comparable_key in seen:
                    raise ValueError(f"clave natural duplicada: {key}")
                seen.add(comparable_key)
                table_records.append(PreparedRecord(remote_record["id"], key, values, links))
            except NonIntegralValue as error:
                issues.append(
                    Issue(
                        "warning",
                        "incompatible_sqlite_type",
                        str(error),
                        spec.airtable_table,
                        key_hint(),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                issues.append(
                    Issue(
                        "error",
                        "invalid_remote_record",
                        str(error),
                        spec.airtable_table,
                        key_hint(),
                    )
                )
        prepared[spec.airtable_table] = table_records
    return prepared, issues


def _local_natural_for_id(
    session: Session, target_spec: TableSpec, row_id: int | None
) -> str | None:
    if row_id is None:
        return None
    target = session.get(target_spec.model, row_id)
    if target is None or len(target_spec.key_attrs) != 1:
        return None
    return str(getattr(target, target_spec.key_attrs[0]))


def _local_key(
    session: Session, spec: TableSpec, obj: Any, mapping: dict[str, Any]
) -> tuple[Any, ...]:
    parts: list[Any] = []
    for key_attr in spec.key_attrs:
        linked_field = next(
            (name for name, attr in mapping["fields"].items() if attr == key_attr and name in spec.links),
            None,
        )
        if linked_field:
            target = SPEC_BY_TABLE[spec.links[linked_field].target_table]
            parts.append(_local_natural_for_id(session, target, getattr(obj, key_attr)))
        else:
            parts.append(getattr(obj, key_attr))
    return tuple(parts)


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.strip() == right.strip()
    return left == right


def plan_records(
    session: Session,
    prepared: dict[str, list[PreparedRecord]],
    field_map: dict[str, Any],
) -> tuple[dict[str, list[PlannedRecord]], list[Issue]]:
    plan: dict[str, list[PlannedRecord]] = {}
    issues: list[Issue] = []
    for spec in TABLE_SPECS:
        mapping = field_map["tables"][spec.airtable_table]
        local_index: dict[tuple[Any, ...], Any] = {}
        for obj in session.scalars(select(spec.model)).all():
            key = _local_key(session, spec, obj, mapping)
            comparable = tuple(value.casefold() if isinstance(value, str) else value for value in key)
            if comparable in local_index:
                issues.append(Issue("error", "duplicate_local_key", f"Clave local duplicada: {key}", spec.airtable_table))
            else:
                local_index[comparable] = obj

        table_plan: list[PlannedRecord] = []
        for record in prepared[spec.airtable_table]:
            comparable = tuple(value.casefold() if isinstance(value, str) else value for value in record.key)
            obj = local_index.get(comparable)
            if obj is None:
                table_plan.append(PlannedRecord("create", record, tuple(record.values) + tuple(record.links)))
                continue
            changed: list[str] = []
            for attr, desired in record.values.items():
                if not _same(getattr(obj, attr), desired):
                    changed.append(attr)
            for source_field, desired_keys in record.links.items():
                link = spec.links[source_field]
                target_spec = SPEC_BY_TABLE[link.target_table]
                target_attr = mapping["fields"][source_field]
                if link.many:
                    existing = {
                        str(item.role.role_key)
                        for item in obj.roles
                        if item.role is not None
                    }
                    if set(desired_keys) - existing:
                        changed.append(source_field)
                else:
                    current = _local_natural_for_id(session, target_spec, getattr(obj, target_attr))
                    desired = desired_keys[0] if desired_keys else None
                    if not _same(current, desired):
                        changed.append(source_field)
            action = "update" if changed else "unchanged"
            table_plan.append(PlannedRecord(action, record, tuple(changed)))
        plan[spec.airtable_table] = table_plan
    return plan, issues


def _lookup_target(session: Session, table: str, natural_key: str) -> Any:
    spec = SPEC_BY_TABLE[table]
    attr = getattr(spec.model, spec.key_attrs[0])
    target = session.scalar(select(spec.model).where(attr == natural_key))
    if target is None:
        raise ValueError(f"No existe destino SQLite {table}.{natural_key}")
    return target


def apply_plan(
    session: Session, plan: dict[str, list[PlannedRecord]], field_map: dict[str, Any]
) -> None:
    for spec in TABLE_SPECS:
        mapping = field_map["tables"][spec.airtable_table]
        for item in plan[spec.airtable_table]:
            if item.action == "unchanged":
                continue
            comparable = tuple(
                value.casefold() if isinstance(value, str) else value
                for value in item.prepared.key
            )
            obj = None
            for candidate in session.scalars(select(spec.model)).all():
                key = _local_key(session, spec, candidate, mapping)
                candidate_key = tuple(value.casefold() if isinstance(value, str) else value for value in key)
                if candidate_key == comparable:
                    obj = candidate
                    break
            resolved_links: dict[str, list[Any]] = {}
            for source_field, desired_keys in item.prepared.links.items():
                link = spec.links[source_field]
                resolved_links[source_field] = [
                    _lookup_target(session, link.target_table, natural_key)
                    for natural_key in desired_keys
                ]
            if obj is None:
                obj = spec.model()
                session.add(obj)
            for attr, value in item.prepared.values.items():
                setattr(obj, attr, value)
            for source_field, desired_keys in item.prepared.links.items():
                link = spec.links[source_field]
                if link.many:
                    existing = {entry.role.role_key for entry in obj.roles if entry.role is not None}
                    for role_key in desired_keys:
                        if role_key not in existing:
                            target = next(
                                target
                                for target in resolved_links[source_field]
                                if target.role_key == role_key
                            )
                            obj.roles.append(EmployeeRole(role=target))
                    continue
                target_attr = mapping["fields"][source_field]
                target = resolved_links[source_field][0] if desired_keys else None
                setattr(obj, target_attr, target.id if target else None)
            session.flush()


def _run_preflight_command(arguments: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, f"{result.stdout}\n{result.stderr}".strip()


def run_preflight(*, max_seed_changes: int, max_seed_ratio: float) -> tuple[list[str], list[Issue]]:
    checks: list[str] = []
    issues: list[Issue] = []
    drift_code, drift_output = _run_preflight_command(["airtable/scripts/check_airtable_drift.py"])
    warnings_match = re.search(r"Warnings:\s*(\d+)", drift_output)
    errors_match = re.search(r"Errores:\s*(\d+)", drift_output)
    drift_warnings = int(warnings_match.group(1)) if warnings_match else -1
    drift_errors = int(errors_match.group(1)) if errors_match else -1
    if drift_code or drift_warnings != 0 or drift_errors != 0:
        issues.append(Issue("error", "airtable_drift_failed", drift_output[-2000:]))
    else:
        checks.append("Drift Airtable: OK, 0 warnings, 0 errores.")

    seed_code, seed_output = _run_preflight_command(
        ["airtable/scripts/seed_airtable_from_excel.py", "--dry-run"]
    )
    changes = sum(
        int(created) + int(updated)
        for created, updated in re.findall(r"creates=(\d+) updates=(\d+)", seed_output)
    )
    upserts = sum(int(value) for value in re.findall(r"upserts=(\d+)", seed_output))
    # Current seed CLI does not print upserts; derive the denominator from all outcomes.
    if not upserts:
        rows = re.findall(
            r"creates=(\d+) updates=(\d+) unchanged=(\d+) skipped=(\d+)", seed_output
        )
        upserts = sum(sum(int(value) for value in row) for row in rows)
    ratio = changes / upserts if upserts else 0.0
    if seed_code:
        issues.append(Issue("error", "airtable_seed_preflight_failed", seed_output[-2000:]))
    elif changes > max_seed_changes and ratio > max_seed_ratio:
        issues.append(
            Issue("error", "airtable_seed_massive_pending", f"Seed pendiente: {changes}/{upserts} cambios ({ratio:.1%}).")
        )
    else:
        checks.append(f"Seed Airtable dry-run: {changes} cambios pendientes de {upserts} registros ({ratio:.1%}).")
    return checks, issues


def validate_sqlite(engine: Any) -> list[Issue]:
    issues: list[Issue] = []
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        actual = set(inspect(engine).get_table_names())
        missing = sorted({spec.model.__tablename__ for spec in TABLE_SPECS} - actual)
        if missing:
            issues.append(Issue("error", "missing_sqlite_tables", f"Tablas faltantes: {', '.join(missing)}"))
    except Exception as error:  # SQLAlchemy wraps driver-specific failures.
        issues.append(Issue("error", "sqlite_unavailable", str(error)))
    return issues


def render_report(plan: PullPlan, *, mode: str, executed: bool) -> str:
    lines = [
        "# Airtable -> SQLite pull report",
        "",
        f"Modo: {mode}",
        f"Cambios aplicados: {'sí' if executed else 'no'}",
        "Política: upsert sin deletes; solo campos incluidos en field_map.v1.json.",
        "",
        "## Pre-flight",
        "",
        *[f"- {check}" for check in plan.preflight],
    ]
    if not plan.preflight:
        lines.append("- Sin checks completados.")
    lines.extend(
        [
            "",
            "## Resumen por tabla",
            "",
            "| Airtable | SQLite | Remotos | Create | Update | Unchanged | Skipped | Error |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for spec in TABLE_SPECS:
        summary = plan.summary(spec.airtable_table)
        lines.append(
            f"| {spec.airtable_table} | `{spec.model.__tablename__}` | {plan.remote_counts.get(spec.airtable_table, 0)} | "
            f"{summary['create']} | {summary['update']} | {summary['unchanged']} | "
            f"{summary['skipped']} | {summary['error']} |"
        )
    lines.extend(["", "## Tablas no soportadas", ""])
    lines.extend(f"- {table}: {reason}" for table, reason in UNSUPPORTED_TABLES.items())
    lines.extend(["", "## Detalle de cambios", ""])
    for spec in TABLE_SPECS:
        changed = [
            item
            for item in plan.records.get(spec.airtable_table, [])
            if item.action in {"create", "update"}
        ]
        if not changed:
            continue
        lines.append(f"### {spec.airtable_table}")
        lines.append("")
        for item in changed:
            fields = ", ".join(item.changed_fields) or "(sin campos)"
            lines.append(f"- {item.action}: `{item.prepared.label}` ({fields})")
        lines.append("")
    lines.extend(["", "## Warnings y errores", ""])
    for issue in plan.issues:
        location = ".".join(part for part in (issue.table, issue.key) if part)
        lines.append(f"- {issue.level}/{issue.code}{f' [{location}]' if location else ''}: {issue.message}")
    if not plan.issues:
        lines.append("- (sin hallazgos)")
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
    parser.add_argument("--max-seed-changes", type=int, default=25)
    parser.add_argument("--max-seed-change-ratio", type=float, default=0.20)
    return parser.parse_args(argv)


def run_pull(
    args: argparse.Namespace,
    *,
    run_remote_preflight: bool = True,
    client: AirtableRecordsClient | None = None,
) -> PullPlan:
    mode = "execute" if args.execute else "dry-run"
    if args.execute and args.confirm != CONFIRM_TEXT:
        raise ValueError(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")

    issues: list[Issue] = []
    checks: list[str] = []
    if run_remote_preflight:
        checks, preflight_issues = run_preflight(
            max_seed_changes=args.max_seed_changes,
            max_seed_ratio=args.max_seed_change_ratio,
        )
        issues.extend(preflight_issues)
    try:
        field_map = _read_json(args.field_map)
        airtable_schema = _read_json(args.airtable_schema)
        issues.extend(validate_field_map(field_map, airtable_schema))
    except (OSError, json.JSONDecodeError) as error:
        field_map = {"tables": {}}
        issues.append(Issue("error", "field_map_unavailable", str(error)))

    engine = create_engine(args.database_url)
    sqlite_issues = validate_sqlite(engine)
    issues.extend(sqlite_issues)
    if not sqlite_issues:
        checks.append("SQLite: conexión y tablas destino accesibles.")

    remote: dict[str, list[dict[str, Any]]] = {spec.airtable_table: [] for spec in TABLE_SPECS}
    plan_records_by_table: dict[str, list[PlannedRecord]] = {spec.airtable_table: [] for spec in TABLE_SPECS}
    if not any(issue.level == "error" for issue in issues):
        try:
            records_client = client or AirtableRecordsClient.from_env()
            remote = fetch_remote_records(records_client, field_map)
            checks.append("Airtable Records API: lectura de tablas soportadas OK.")
            remote_indexes, index_issues = build_remote_indexes(remote, field_map)
            issues.extend(index_issues)
            prepared, preparation_issues = prepare_records(remote, field_map, remote_indexes)
            issues.extend(preparation_issues)
            with Session(engine) as session:
                plan_records_by_table, planning_issues = plan_records(session, prepared, field_map)
                issues.extend(planning_issues)
        except (AirtableRecordsError, KeyError, ValueError) as error:
            issues.append(Issue("error", "airtable_read_failed", str(error)))

    pull_plan = PullPlan(
        plan_records_by_table,
        issues,
        {table: len(records) for table, records in remote.items()},
        checks,
    )
    executed = False
    if args.execute and not any(issue.level == "error" for issue in issues):
        try:
            with Session(engine) as session, session.begin():
                apply_plan(session, plan_records_by_table, field_map)
            executed = True
        except Exception as error:
            issues.append(Issue("error", "sqlite_transaction_rolled_back", str(error)))

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(pull_plan, mode=mode, executed=executed), encoding="utf-8")
    return pull_plan


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.execute and args.confirm != CONFIRM_TEXT:
        raise SystemExit(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")
    pull_plan = run_pull(args)
    mode = "execute" if args.execute else "dry-run"
    print(f"MODE: {mode}")
    for spec in TABLE_SPECS:
        summary = pull_plan.summary(spec.airtable_table)
        print(
            f"{spec.airtable_table}: creates={summary['create']} updates={summary['update']} "
            f"unchanged={summary['unchanged']} skipped={summary['skipped']} errors={summary['error']}"
        )
    print(f"Warnings: {sum(issue.level == 'warning' for issue in pull_plan.issues)}")
    print(f"Errores: {sum(issue.level == 'error' for issue in pull_plan.issues)}")
    print(f"Reporte: {args.report}")
    return 1 if any(issue.level == "error" for issue in pull_plan.issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
