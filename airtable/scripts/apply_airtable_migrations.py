"""Runner de migraciones Airtable tipo Alembic para Kanpai POS.

Modos:
- dry-run por defecto.
- inspect lee schema real.
- execute aplica migraciones pendientes y registra ledger remoto.

Requiere para execute:
- AIRTABLE_API_TOKEN
- AIRTABLE_BASE_ID
- scopes: schema.bases:read/write + data.records:read/write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

META_ROOT = "https://api.airtable.com/v0/meta/bases"
DATA_ROOT = "https://api.airtable.com/v0"
CONFIRM_TEXT = "APPLY_KANPAI_AIRTABLE_MIGRATIONS"
DEFAULT_MIGRATIONS_DIR = Path("airtable/migrations")
DEFAULT_REPORT = Path("airtable/reports/airtable_migrations_report.md")
LEDGER_TABLE = "_AirtableSchemaMigrations"


class MigrationError(RuntimeError):
    pass


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def request_json(
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, 5):
        request = Request(url, data=data, headers=headers, method=method)

        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")

            if error.code == 429 and attempt < 4:
                time.sleep(31)
                continue

            if error.code in {500, 502, 503} and attempt < 4:
                time.sleep(min(2**attempt, 10))
                continue

            raise MigrationError(f"Airtable HTTP {error.code}: {method} {url}: {detail}") from error
        except URLError as error:
            if attempt < 4:
                time.sleep(min(2**attempt, 10))
                continue

            raise MigrationError(f"Airtable network error: {method} {url}: {error}") from error

    raise MigrationError(f"No se pudo completar {method} {url}.")


def migration_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_migrations(migrations_dir: Path) -> list[dict[str, Any]]:
    migrations = []

    for path in sorted(migrations_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_path"] = str(path)
        payload["_checksum"] = migration_checksum(path)
        migrations.append(payload)

    revisions = [item["revision"] for item in migrations]
    if len(revisions) != len(set(revisions)):
        raise MigrationError("Hay revisiones duplicadas.")

    known = set(revisions)
    for item in migrations:
        down = item.get("down_revision")
        if down is not None and down not in known:
            raise MigrationError(f"{item['revision']}: down_revision inexistente: {down}")

    return migrations


def fetch_schema(base_id: str, token: str) -> dict[str, Any]:
    return request_json("GET", f"{META_ROOT}/{base_id}/tables", token)


def schema_index(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}

    for table in schema.get("tables", []):
        result[table["name"]] = {
            "id": table["id"],
            "fields": {field["name"]: field for field in table.get("fields", [])},
        }

    return result


def clean_field_payload(field: dict[str, Any], table_ids: dict[str, str] | None = None) -> dict[str, Any]:
    payload = {
        "name": field["name"],
        "type": field["type"],
    }

    options = field.get("options")

    if field["type"] == "multipleRecordLinks":
        if not options:
            raise MigrationError(f"Campo link sin options: {field['name']}")

        linked_table_name = options.get("linkedTableName")
        linked_table_id = options.get("linkedTableId")

        if table_ids and linked_table_name:
            linked_table_id = table_ids.get(linked_table_name)

        if not linked_table_id:
            raise MigrationError(f"No se pudo resolver linkedTableId para {field['name']} -> {linked_table_name}")

        payload["options"] = {"linkedTableId": linked_table_id}
        return payload

    if options:
        payload["options"] = options

    return payload


def create_meta_table(base_id: str, token: str, table_name: str, first_field: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": table_name,
        "fields": [clean_field_payload(first_field)],
    }
    return request_json("POST", f"{META_ROOT}/{base_id}/tables", token, payload)


def create_meta_field(base_id: str, token: str, table_id: str, field: dict[str, Any], table_ids: dict[str, str]) -> dict[str, Any]:
    payload = clean_field_payload(field, table_ids)
    return request_json("POST", f"{META_ROOT}/{base_id}/tables/{table_id}/fields", token, payload)


def list_records(base_id: str, token: str, table_name: str, fields: list[str] | None = None) -> list[dict[str, Any]]:
    records = []
    offset = None
    encoded_table = quote(table_name, safe="")

    while True:
        params: dict[str, Any] = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        if fields:
            for index, field in enumerate(fields):
                params[f"fields[{index}]"] = field

        url = f"{DATA_ROOT}/{base_id}/{encoded_table}?{urlencode(params)}"
        response = request_json("GET", url, token)
        records.extend(response.get("records", []))
        offset = response.get("offset")

        if not offset:
            break

    return records


def create_record(base_id: str, token: str, table_name: str, fields: dict[str, Any]) -> dict[str, Any]:
    encoded_table = quote(table_name, safe="")
    payload = {"records": [{"fields": fields}]}
    return request_json("POST", f"{DATA_ROOT}/{base_id}/{encoded_table}", token, payload)


def ensure_ledger_table(base_id: str, token: str, actions: list[str], skipped: list[str]) -> None:
    schema = fetch_schema(base_id, token)
    index = schema_index(schema)

    if LEDGER_TABLE not in index:
        created = create_meta_table(
            base_id,
            token,
            LEDGER_TABLE,
            {"name": "revision", "type": "singleLineText"},
        )
        actions.append(f"LEDGER TABLA CREADA: {LEDGER_TABLE}")
        time.sleep(0.25)
        table_id = created["id"]
        existing_fields = {"revision"}
    else:
        table_id = index[LEDGER_TABLE]["id"]
        existing_fields = set(index[LEDGER_TABLE]["fields"])
        skipped.append(f"LEDGER TABLA EXISTE: {LEDGER_TABLE}")

    required_fields = [
        {"name": "down_revision", "type": "singleLineText"},
        {"name": "checksum", "type": "singleLineText"},
        {"name": "applied_at", "type": "dateTime", "options": {"dateFormat": {"name": "iso"}, "timeFormat": {"name": "24hour"}, "timeZone": "America/Mexico_City"}},
        {"name": "status", "type": "singleSelect", "options": {"choices": [{"name": "Aplicada"}, {"name": "Fallida"}]}},
        {"name": "report", "type": "multilineText"},
    ]

    for field in required_fields:
        if field["name"] in existing_fields:
            skipped.append(f"LEDGER CAMPO EXISTE: {LEDGER_TABLE}.{field['name']}")
            continue

        create_meta_field(base_id, token, table_id, field, {})
        actions.append(f"LEDGER CAMPO CREADO: {LEDGER_TABLE}.{field['name']}")
        time.sleep(0.25)


def applied_revisions(base_id: str, token: str) -> dict[str, dict[str, Any]]:
    records = list_records(base_id, token, LEDGER_TABLE, fields=["revision", "checksum", "status"])
    result = {}

    for record in records:
        fields = record.get("fields", {})
        revision = fields.get("revision")
        if revision:
            result[revision] = fields

    return result


def mark_migration_applied(
    base_id: str,
    token: str,
    migration: dict[str, Any],
    report: str,
) -> None:
    create_record(
        base_id,
        token,
        LEDGER_TABLE,
        {
            "revision": migration["revision"],
            "down_revision": migration.get("down_revision") or "",
            "checksum": migration["_checksum"],
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "status": "Aplicada",
            "report": report[:90000],
        },
    )


def ensure_table_with_direct_fields(
    base_id: str,
    token: str,
    op: dict[str, Any],
    index: dict[str, dict[str, Any]],
    actions: list[str],
    skipped: list[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    table_name = op["table"]
    fields = op.get("fields", [])

    if not fields:
        errors.append(f"{table_name}: ensure_table sin campos")
        return index

    if table_name not in index:
        create_meta_table(base_id, token, table_name, fields[0])
        actions.append(f"TABLA CREADA: {table_name}")
        time.sleep(0.25)
        index = schema_index(fetch_schema(base_id, token))
    else:
        skipped.append(f"TABLA EXISTE: {table_name}")

    table_id = index[table_name]["id"]

    for field in fields[1:]:
        field_name = field["name"]
        if field_name in index[table_name]["fields"]:
            skipped.append(f"CAMPO EXISTE: {table_name}.{field_name}")
            continue

        try:
            create_meta_field(base_id, token, table_id, field, {})
            actions.append(f"CAMPO CREADO: {table_name}.{field_name}")
            time.sleep(0.25)
            index = schema_index(fetch_schema(base_id, token))
        except MigrationError as error:
            errors.append(str(error))

    return index


def ensure_late_field(
    base_id: str,
    token: str,
    op: dict[str, Any],
    index: dict[str, dict[str, Any]],
    actions: list[str],
    skipped: list[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    table_name = op["table"]
    field = op["field"]
    field_name = field["name"]

    if table_name not in index:
        errors.append(f"Tabla faltante para campo tardio: {table_name}.{field_name}")
        return index

    if field_name in index[table_name]["fields"]:
        skipped.append(f"CAMPO TARDIO EXISTE: {table_name}.{field_name}")
        return index

    table_ids = {name: info["id"] for name, info in index.items()}
    table_id = index[table_name]["id"]

    try:
        create_meta_field(base_id, token, table_id, field, table_ids)
        actions.append(f"CAMPO TARDIO CREADO: {table_name}.{field_name}")
        time.sleep(0.25)
        return schema_index(fetch_schema(base_id, token))
    except MigrationError as error:
        errors.append(str(error))
        return index


def execute_migrations(
    migrations: list[dict[str, Any]],
    base_id: str,
    token: str,
) -> tuple[list[str], list[str], list[str]]:
    actions: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    ensure_ledger_table(base_id, token, actions, skipped)
    applied = applied_revisions(base_id, token)
    index = schema_index(fetch_schema(base_id, token))

    for migration in migrations:
        revision = migration["revision"]
        checksum = migration["_checksum"]

        if revision in applied:
            if applied[revision].get("checksum") != checksum:
                errors.append(f"{revision}: checksum remoto no coincide; no se puede reaplicar.")
            else:
                skipped.append(f"MIGRATION YA APLICADA: {revision}")
            continue

        if migration.get("destructive"):
            errors.append(f"{revision}: migracion destructiva bloqueada.")
            continue

        actions.append(f"MIGRATION APLICANDO: {revision}")

        before_errors = len(errors)

        for op in migration.get("operations", []):
            op_name = op.get("op")

            if op_name == "ensure_table":
                index = ensure_table_with_direct_fields(base_id, token, op, index, actions, skipped, errors)
            elif op_name == "ensure_field":
                index = ensure_late_field(base_id, token, op, index, actions, skipped, errors)
            else:
                errors.append(f"{revision}: op no soportada: {op_name}")

        if len(errors) == before_errors:
            mark_migration_applied(
                base_id,
                token,
                migration,
                report=f"Migracion aplicada correctamente: {revision}",
            )
            actions.append(f"MIGRATION REGISTRADA: {revision}")
            time.sleep(0.25)
        else:
            errors.append(f"{revision}: no se registro ledger por errores.")

    return actions, skipped, errors


def dry_run(migrations: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    actions = []
    warnings = []
    errors = []

    for migration in migrations:
        actions.append(f"MIGRATION PENDIENTE: {migration['revision']} - {migration.get('description', '')}")

        for op in migration.get("operations", []):
            op_name = op.get("op")

            if op_name == "ensure_table":
                actions.append(f"  ensure_table {op['table']} ({len(op.get('fields', []))} campos directos)")
            elif op_name == "ensure_field":
                actions.append(f"  ensure_field {op['table']}.{op['field']['name']}")
            else:
                errors.append(f"{migration['revision']}: op no soportada: {op_name}")

    return actions, warnings, errors


def inspect_remote(base_id: str, token: str) -> tuple[list[str], list[str], list[str]]:
    schema = fetch_schema(base_id, token)
    tables = schema.get("tables", [])

    actions = [
        f"BASE REMOTA OK: {base_id}",
        f"TABLAS REMOTAS: {len(tables)}",
    ]
    warnings = []
    errors = []

    for table in tables:
        actions.append(f"  {table['name']} ({table['id']}) campos={len(table.get('fields', []))}")

    if any(table["name"] == "Table 1" for table in tables):
        warnings.append("Existe Table 1 bootstrap. No se borra por script.")

    if not any(table["name"] == LEDGER_TABLE for table in tables):
        warnings.append(f"No existe {LEDGER_TABLE}. Se creará al ejecutar migraciones.")

    return actions, warnings, errors


def render_report(
    mode: str,
    actions: list[str],
    warnings: list[str],
    errors: list[str],
    skipped: list[str] | None = None,
) -> str:
    skipped = skipped or []
    lines = [
        "# Airtable migrations report",
        "",
        f"Modo: {mode}",
        "",
        "## Acciones",
        "",
        *[f"- {item}" for item in actions or ["(sin acciones)"]],
        "",
        "## Omitidos",
        "",
        *[f"- {item}" for item in skipped or ["(sin omitidos)"]],
        "",
        "## Warnings",
        "",
        *[f"- {item}" for item in warnings or ["(sin warnings)"]],
        "",
        "## Errores",
        "",
        *[f"- {item}" for item in errors or ["(sin errores)"]],
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrations-dir", type=Path, default=DEFAULT_MIGRATIONS_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    return parser.parse_args()


def require_remote_env() -> tuple[str, str]:
    token = os.getenv("AIRTABLE_API_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")

    if not token:
        raise SystemExit("Falta AIRTABLE_API_TOKEN.")
    if not base_id:
        raise SystemExit("Falta AIRTABLE_BASE_ID.")

    return base_id, token


def main() -> int:
    load_dotenv()
    args = parse_args()
    skipped: list[str] = []

    if args.inspect:
        base_id, token = require_remote_env()
        actions, warnings, errors = inspect_remote(base_id, token)
        mode = "inspect"
    else:
        migrations = load_migrations(args.migrations_dir)

        if args.execute:
            if args.confirm != CONFIRM_TEXT:
                raise SystemExit(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")

            base_id, token = require_remote_env()
            actions, skipped, errors = execute_migrations(migrations, base_id, token)
            warnings = []
            mode = "execute"
        else:
            actions, warnings, errors = dry_run(migrations)
            mode = "dry-run"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(mode, actions, warnings, errors, skipped), encoding="utf-8")

    print(f"MODE: {mode}")
    print(f"Acciones: {len(actions)}")
    print(f"Omitidos: {len(skipped)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errores: {len(errors)}")
    print(f"Reporte: {args.report}")

    if errors:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
