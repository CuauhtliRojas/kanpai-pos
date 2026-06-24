"""Safe production reset of Airtable operational (readonly mirror) tables.

Default mode is preview — no remote records are mutated.
To delete, both --execute and --confirm PREPARE_KANPAI_AIRTABLE_PRODUCTION_RESET
are required. Catalog and configuration tables are permanently blocked.

Typical usage:
    # Preview (safe, no changes):
    uv run python airtable/scripts/prepare_airtable_production_reset.py

    # Execute (only after previewing and confirming intent):
    uv run python airtable/scripts/prepare_airtable_production_reset.py \\
        --execute --confirm PREPARE_KANPAI_AIRTABLE_PRODUCTION_RESET
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for _import_path in (ROOT, SCRIPT_DIR):
    if str(_import_path) not in sys.path:
        sys.path.insert(0, str(_import_path))

from airtable_records_client import AirtableRecordsClient, AirtableRecordsError  # noqa: E402

CONFIRM_TEXT = "PREPARE_KANPAI_AIRTABLE_PRODUCTION_RESET"
DEFAULT_FIELD_MAP = ROOT / "airtable/schema/field_map.v1.json"

OPERATIONAL_DIRECTION = "push_to_airtable_readonly"
CATALOG_DIRECTION = "pull_to_sqlite"

# Explicit allowlist — only operational readonly-mirror tables.
# Every entry must exist in field_map.v1.json with direction == OPERATIONAL_DIRECTION.
# Catalog, configuration, and any pull_to_sqlite table is unconditionally blocked.
OPERATIONAL_ALLOWLIST: tuple[str, ...] = (
    "CortesCaja",
    "Tickets",
    "LineasTicket",
    "Pagos",
    "TrabajosImpresion",
    "HistorialSMS",
    "EventosAuditoria",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_allowlist(field_map: dict[str, Any]) -> list[str]:
    """Return validation errors; empty list means allowlist is safe to use."""
    tables = field_map.get("tables", {})
    errors: list[str] = []
    for table in OPERATIONAL_ALLOWLIST:
        mapping = tables.get(table)
        if mapping is None:
            errors.append(f"{table}: no encontrada en field_map.v1.json")
            continue
        direction = mapping.get("direction", "")
        if direction == CATALOG_DIRECTION:
            errors.append(
                f"{table}: dirección '{direction}' — tabla de catálogo bloqueada"
            )
        elif direction != OPERATIONAL_DIRECTION:
            errors.append(
                f"{table}: dirección '{direction}' — se esperaba '{OPERATIONAL_DIRECTION}'"
            )
    return errors


def run_preview(
    client: AirtableRecordsClient,
    field_map: dict[str, Any],
) -> dict[str, int]:
    """List remote records per allowlist table. Returns {table: count}. No mutations."""
    errors = validate_allowlist(field_map)
    if errors:
        raise ValueError("Allowlist inválida:\n" + "\n".join(f"  {e}" for e in errors))
    return {
        table: len(client.list_records(table, fields=["id_sqlite"]))
        for table in OPERATIONAL_ALLOWLIST
    }


def run_execute(
    client: AirtableRecordsClient,
    field_map: dict[str, Any],
) -> dict[str, int]:
    """Delete all records in allowlist tables. Returns {table: deleted_count}.

    Caller is responsible for checking confirmation before invoking this function.
    """
    errors = validate_allowlist(field_map)
    if errors:
        raise ValueError("Allowlist inválida:\n" + "\n".join(f"  {e}" for e in errors))
    result: dict[str, int] = {}
    for table in OPERATIONAL_ALLOWLIST:
        record_ids = [r["id"] for r in client.list_records(table, fields=["id_sqlite"])]
        result[table] = client.delete_records(table, record_ids) if record_ids else 0
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset Airtable operational mirror tables (preview or execute)."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete records (requires --confirm).",
    )
    parser.add_argument(
        "--confirm",
        default="",
        metavar="TOKEN",
        help=f"Must be '{CONFIRM_TEXT}' when --execute is set.",
    )
    parser.add_argument(
        "--field-map",
        type=Path,
        default=DEFAULT_FIELD_MAP,
        metavar="PATH",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.execute and args.confirm != CONFIRM_TEXT:
        raise SystemExit(
            f"Para borrar usa --execute --confirm {CONFIRM_TEXT}\n"
            f"Recibido: '{args.confirm}'"
        )

    try:
        field_map = _read_json(args.field_map)
    except OSError as error:
        print(f"ERROR: no se pudo leer field_map: {error}", file=sys.stderr)
        return 1

    errors = validate_allowlist(field_map)
    if errors:
        print("ERROR: allowlist inválida — abortando sin tocar Airtable:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1

    try:
        client = AirtableRecordsClient.from_env()
    except (AirtableRecordsError, ValueError) as error:
        print(f"ERROR: cliente Airtable: {error}", file=sys.stderr)
        return 1

    try:
        if not args.execute:
            counts = run_preview(client, field_map)
            total = sum(counts.values())
            print("=== PREVIEW ONLY — ningún registro será borrado ===")
            print()
            for table in OPERATIONAL_ALLOWLIST:
                print(f"  {table}: {counts[table]:>6} registros remotos")
            print()
            print(f"  Total: {total} registros se borrarían con --execute")
            print()
            print("Para borrar ejecuta con:")
            print(f"  --execute --confirm {CONFIRM_TEXT}")
            return 0

        deleted = run_execute(client, field_map)
        total = sum(deleted.values())
        print("=== RESET AIRTABLE EJECUTADO ===")
        print()
        for table in OPERATIONAL_ALLOWLIST:
            print(f"  {table}: {deleted[table]:>6} registros borrados")
        print()
        print(f"  Total: {total} registros borrados")
        return 0

    except (AirtableRecordsError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
