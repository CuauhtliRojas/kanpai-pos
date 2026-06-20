"""Verificador de drift Airtable para Kanpai POS.

Compara:
- airtable/schema/kanpai_airtable_schema.v1.json
contra
- schema real remoto en Airtable Metadata API

Errores:
- tabla requerida faltante
- campo requerido faltante
- tipo requerido cambiado

Warnings:
- Table 1 bootstrap
- _AirtableSchemaMigrations presente
- tabla extra
- campo extra

No modifica Airtable.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

META_ROOT = "https://api.airtable.com/v0/meta/bases"
DEFAULT_SCHEMA = Path("airtable/schema/kanpai_airtable_schema.v1.json")
DEFAULT_REPORT = Path("airtable/reports/airtable_drift_report.md")

TYPE_MAP = {
    "singleLineText": "singleLineText",
    "multilineText": "multilineText",
    "number": "number",
    "checkbox": "checkbox",
    "singleSelect": "singleSelect",
    "dateTime": "dateTime",
    "formula": "formula",
    "link": "multipleRecordLinks",
}

KNOWN_EXTRA_TABLES = {
    "Table 1",
    "_AirtableSchemaMigrations",
}


class DriftError(RuntimeError):
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


def request_json(method: str, url: str, token: str) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, 5):
        request = Request(url, headers=headers, method=method)

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

            raise DriftError(f"Airtable HTTP {error.code}: {method} {url}: {detail}") from error
        except URLError as error:
            if attempt < 4:
                time.sleep(min(2**attempt, 10))
                continue

            raise DriftError(f"Airtable network error: {method} {url}: {error}") from error

    raise DriftError(f"No se pudo completar {method} {url}.")


def require_remote_env() -> tuple[str, str]:
    token = os.getenv("AIRTABLE_API_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")

    if not token:
        raise SystemExit("Falta AIRTABLE_API_TOKEN.")
    if not base_id:
        raise SystemExit("Falta AIRTABLE_BASE_ID.")

    return base_id, token


def fetch_remote_schema(base_id: str, token: str) -> dict[str, Any]:
    return request_json("GET", f"{META_ROOT}/{base_id}/tables", token)


def expected_index(schema: dict[str, Any]) -> dict[str, dict[str, str]]:
    result = {}

    for table in schema["tables"]:
        fields = {}

        for field in table["fields"]:
            expected_type = TYPE_MAP[field["type"]]
            fields[field["name"]] = expected_type

        result[table["name"]] = fields

    return result


def remote_index(remote_schema: dict[str, Any]) -> dict[str, dict[str, str]]:
    result = {}

    for table in remote_schema.get("tables", []):
        fields = {}

        for field in table.get("fields", []):
            fields[field["name"]] = field["type"]

        result[table["name"]] = fields

    return result


def check_drift(
    expected: dict[str, dict[str, str]],
    remote: dict[str, dict[str, str]],
) -> tuple[list[str], list[str], list[str]]:
    ok = []
    warnings = []
    errors = []
    controlled = []

    for table_name, expected_fields in expected.items():
        if table_name not in remote:
            errors.append(f"TABLA FALTANTE: {table_name}")
            continue

        ok.append(f"TABLA OK: {table_name}")

        remote_fields = remote[table_name]

        for field_name, expected_type in expected_fields.items():
            if field_name not in remote_fields:
                errors.append(f"CAMPO FALTANTE: {table_name}.{field_name}")
                continue

            remote_type = remote_fields[field_name]

            if remote_type != expected_type:
                errors.append(
                    f"TIPO CAMBIADO: {table_name}.{field_name} esperado={expected_type} remoto={remote_type}"
                )
                continue

            ok.append(f"CAMPO OK: {table_name}.{field_name}")

        for remote_field_name in sorted(set(remote_fields) - set(expected_fields)):
            remote_type = remote_fields[remote_field_name]

            if remote_type == "multipleRecordLinks":
                controlled.append(f"BACKLINK AIRTABLE: {table_name}.{remote_field_name}")
                continue

            warnings.append(f"CAMPO EXTRA: {table_name}.{remote_field_name}")

    for remote_table_name in sorted(set(remote) - set(expected)):
        if remote_table_name in KNOWN_EXTRA_TABLES:
            controlled.append(f"TABLA EXTRA CONTROLADA: {remote_table_name}")
        else:
            warnings.append(f"TABLA EXTRA: {remote_table_name}")

    ok.extend(controlled)
    return ok, warnings, errors


def render_report(
    *,
    base_id: str,
    ok: list[str],
    warnings: list[str],
    errors: list[str],
) -> str:
    lines = [
        "# Airtable drift report",
        "",
        f"Base: {base_id}",
        "",
        "## Resumen",
        "",
        f"- OK/controlados: {len(ok)}",
        f"- Warnings: {len(warnings)}",
        f"- Errores: {len(errors)}",
        "",
        "## Errores",
        "",
        *[f"- {item}" for item in errors or ["(sin errores)"]],
        "",
        "## Warnings",
        "",
        *[f"- {item}" for item in warnings or ["(sin warnings)"]],
        "",
        "## OK",
        "",
        *[f"- {item}" for item in ok],
        "",
    ]

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    base_id, token = require_remote_env()

    expected_schema = json.loads(args.schema.read_text(encoding="utf-8"))
    remote_schema = fetch_remote_schema(base_id, token)

    ok, warnings, errors = check_drift(
        expected_index(expected_schema),
        remote_index(remote_schema),
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_report(base_id=base_id, ok=ok, warnings=warnings, errors=errors),
        encoding="utf-8",
    )

    print("AIRTABLE DRIFT CHECK")
    print(f"Base: {base_id}")
    print(f"OK: {len(ok)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errores: {len(errors)}")
    print(f"Reporte: {args.report}")

    if errors:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
