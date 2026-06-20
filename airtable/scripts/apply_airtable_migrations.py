"""Runner de migraciones Airtable tipo Alembic para Kanpai POS.

Modo seguro:
- dry-run por defecto.
- inspect lee schema real.
- execute queda bloqueado por confirmación explícita.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_ROOT = "https://api.airtable.com/v0/meta/bases"
CONFIRM_TEXT = "APPLY_KANPAI_AIRTABLE_MIGRATIONS"
DEFAULT_MIGRATIONS_DIR = Path("airtable/migrations")
DEFAULT_REPORT = Path("airtable/reports/airtable_migrations_report.md")


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


def request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    import time

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
    return request_json("GET", f"{API_ROOT}/{base_id}/tables", token)


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

    if not any(table["name"] == "_AirtableSchemaMigrations" for table in tables):
        warnings.append("No existe _AirtableSchemaMigrations. Se creará al ejecutar migraciones.")

    return actions, warnings, errors


def render_report(mode: str, actions: list[str], warnings: list[str], errors: list[str]) -> str:
    lines = [
        "# Airtable migrations report",
        "",
        f"Modo: {mode}",
        "",
        "## Acciones",
        "",
        *[f"- {item}" for item in actions or ["(sin acciones)"]],
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


def main() -> int:
    load_dotenv()
    args = parse_args()

    if args.inspect:
        token = os.getenv("AIRTABLE_API_TOKEN")
        base_id = os.getenv("AIRTABLE_BASE_ID")

        if not token:
            raise SystemExit("Falta AIRTABLE_API_TOKEN.")
        if not base_id:
            raise SystemExit("Falta AIRTABLE_BASE_ID.")

        actions, warnings, errors = inspect_remote(base_id, token)
        mode = "inspect"
    else:
        migrations = load_migrations(args.migrations_dir)

        if args.execute:
            if args.confirm != CONFIRM_TEXT:
                raise SystemExit(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")

            raise SystemExit(
                "execute aun no esta habilitado: falta ledger remoto _AirtableSchemaMigrations "
                "y scopes data.records:read/write."
            )

        actions, warnings, errors = dry_run(migrations)
        mode = "dry-run"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(mode, actions, warnings, errors), encoding="utf-8")

    print(f"MODE: {mode}")
    print(f"Acciones: {len(actions)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errores: {len(errors)}")
    print(f"Reporte: {args.report}")

    if errors:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
