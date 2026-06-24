"""Classify Airtable columns by usage category for cleanup planning.

Works entirely from local files — no Airtable API call unless --remote is passed.

Categories
----------
MAPEADO_PULL   Field is mapped in field_map.v1.json for a pull_to_sqlite table.
MAPEADO_PUSH   Field is mapped in field_map.v1.json for a push_to_airtable_readonly table.
TECNICO_SYNC   Technical sync field written/read internally (id_sqlite, estado_sync…).
               Not in field_map but managed by pull/push scripts.
LINK_SCHEMA    Linked-record field declared in our schema (maps to multipleRecordLinks
               in Airtable). All are also MAPEADO_PULL unless noted.
EXTRA_LOCAL    Field exists in our local schema but is not mapped anywhere and is not
               a known technical field. Candidate for review.
DEPRECATED_FISCAL  Field found in the live Airtable base (reported by drift checker as
               CAMPO EXTRA) but not in our schema — legacy fiscal fields already
               removed from the operational flow.

Usage
-----
    # Local-only analysis (no Airtable call):
    uv run python airtable/scripts/audit_airtable_columns.py

    # With Airtable fetch to discover additional unmapped remote fields:
    uv run python airtable/scripts/audit_airtable_columns.py --remote
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

DEFAULT_FIELD_MAP = ROOT / "airtable/schema/field_map.v1.json"
DEFAULT_SCHEMA = ROOT / "airtable/schema/kanpai_airtable_schema.v1.json"
DEFAULT_REPORT = ROOT / "airtable/reports/airtable_column_audit.md"

# Technical sync fields present in every schema table but NOT in field_map.
# Managed internally by the push/pull scripts.
TECNICO_SYNC_FIELDS: frozenset[str] = frozenset(
    {
        "id_sqlite",       # written by push (is in push field_map); for pull tables: not mapped
        "estado_sync",     # written by push code, never in field_map
        "revision_remota",
        "actualizado_sqlite_en",   # in push field_map; for pull: not mapped
        "actualizado_airtable_en",
        "ultimo_pull_en",
        "ultimo_push_en",
        "error_sync",
    }
)

# Fields that EXIST IN AIRTABLE but are NOT in kanpai_airtable_schema.v1.json.
# Discovered via check_airtable_drift.py (CAMPO EXTRA). Deprecated fiscal flow
# removed in commits 19b2d57 and ac0d62e.
DEPRECATED_FISCAL: dict[str, dict[str, str]] = {
    "ConfiguracionNegocio": {
        "etiqueta_impuesto": "Campo fiscal retirado — impuestos eliminados del flujo (ac0d62e)",
        "impuesto_incluido": "Campo fiscal retirado (ac0d62e)",
        "impuestos_activos": "Campo fiscal retirado (ac0d62e)",
        "tasa_impuesto_bps": "Campo fiscal retirado (ac0d62e)",
    },
    "Tickets": {
        "impuesto_centavos": "Campo fiscal retirado — impuesto eliminado del ticket (19b2d57)",
    },
}

# Schema field types that Airtable manages automatically (read-only computed).
COMPUTED_TYPES: frozenset[str] = frozenset(
    {"formula", "rollup", "lookup", "count", "autoNumber",
     "createdTime", "lastModifiedTime", "lastModifiedBy", "createdBy"}
)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _build_mapped_fields(field_map: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Return {table_name: {field_name: direction}} from field_map."""
    result: dict[str, dict[str, str]] = {}
    for table_name, mapping in field_map.get("tables", {}).items():
        direction = mapping.get("direction", "")
        result[table_name] = {field: direction for field in mapping.get("fields", {})}
    return result


def _classify_field(
    table: str,
    field_name: str,
    field_type: str,
    field_meta: dict[str, Any],
    mapped: dict[str, str],
) -> str:
    """Return the category string for a single field."""
    if field_name in mapped:
        direction = mapped[field_name]
        if direction == "push_to_airtable_readonly":
            return "MAPEADO_PUSH"
        if direction == "pull_to_sqlite":
            return "MAPEADO_PULL"
        return f"MAPEADO_{direction.upper()}"
    if field_name in TECNICO_SYNC_FIELDS:
        return "TECNICO_SYNC"
    if field_type == "link":
        return "EXTRA_LOCAL"  # link fields should all be in field_map; flag if not
    if field_type in COMPUTED_TYPES:
        return "FORMULA_LOOKUP_ROLLUP"
    return "EXTRA_LOCAL"


def _action_for_category(category: str) -> str:
    return {
        "MAPEADO_PULL": "conservar (pull activo)",
        "MAPEADO_PUSH": "conservar (push activo)",
        "TECNICO_SYNC": "conservar (uso interno scripts)",
        "FORMULA_LOOKUP_ROLLUP": "conservar (calculado por Airtable)",
        "EXTRA_LOCAL": "revisar — candidato a borrar o documentar",
        "LINK_SCHEMA": "conservar (link activo)",
    }.get(category, "revisar")


def audit(
    schema: dict[str, Any],
    field_map: dict[str, Any],
    *,
    extra_remote_fields: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Build the full audit dict from local schema + field_map.

    extra_remote_fields: optional {table: [field_name, ...]} from live Airtable fetch.
    """
    mapped_by_table = _build_mapped_fields(field_map)
    tables_direction = {
        name: mapping.get("direction", "")
        for name, mapping in field_map.get("tables", {}).items()
    }

    results: list[dict[str, Any]] = []
    category_totals: dict[str, int] = {}

    for table_entry in schema.get("tables", []):
        table_name = table_entry["name"]
        direction = tables_direction.get(table_name, "not_in_field_map")
        mapped = mapped_by_table.get(table_name, {})

        fields_classified: list[dict[str, str]] = []
        for field in table_entry.get("fields", []):
            field_name = field["name"]
            field_type = field.get("type", "unknown")
            category = _classify_field(table_name, field_name, field_type, field, mapped)
            category_totals[category] = category_totals.get(category, 0) + 1
            fields_classified.append(
                {
                    "field": field_name,
                    "type": field_type,
                    "category": category,
                    "action": _action_for_category(category),
                }
            )

        # Extra fields from live Airtable not in local schema
        extra_fields: list[dict[str, str]] = []
        for extra_field in (extra_remote_fields or {}).get(table_name, []):
            category = "EXTRA_REMOTO"
            category_totals[category] = category_totals.get(category, 0) + 1
            extra_fields.append(
                {
                    "field": extra_field,
                    "type": "unknown_remote",
                    "category": category,
                    "action": "revisar — no está en schema local",
                }
            )

        results.append(
            {
                "table": table_name,
                "direction": direction,
                "fields": fields_classified,
                "extra_remote": extra_fields,
            }
        )

    return {
        "tables": results,
        "totals": category_totals,
        "deprecated_fiscal": DEPRECATED_FISCAL,
    }


def render_report(audit_result: dict[str, Any]) -> str:
    today = date.today().isoformat()
    lines = [
        "# Auditoría de columnas Airtable",
        "",
        f"Generado: {today}",
        "Fuente: `field_map.v1.json` + `kanpai_airtable_schema.v1.json`",
        "",
        "## Categorías",
        "",
        "| Categoría | Significado |",
        "|---|---|",
        "| MAPEADO_PULL | Mapeado en field_map, dirección pull_to_sqlite |",
        "| MAPEADO_PUSH | Mapeado en field_map, dirección push_to_airtable_readonly |",
        "| TECNICO_SYNC | Campo de sincronización interno (id_sqlite, estado_sync…) |",
        "| FORMULA_LOOKUP_ROLLUP | Calculado por Airtable — no editable |",
        "| EXTRA_LOCAL | En schema local pero sin mapeo — revisar |",
        "| EXTRA_REMOTO | En Airtable real pero no en schema local — revisar |",
        "",
        "## Resumen por categoría",
        "",
        "| Categoría | Campos |",
        "|---|---:|",
    ]
    totals = audit_result["totals"]
    for cat in ["MAPEADO_PULL", "MAPEADO_PUSH", "TECNICO_SYNC",
                "FORMULA_LOOKUP_ROLLUP", "EXTRA_LOCAL", "EXTRA_REMOTO"]:
        if totals.get(cat, 0):
            lines.append(f"| {cat} | {totals[cat]} |")
    lines.extend(["", "## Detalle por tabla", ""])

    for table_entry in audit_result["tables"]:
        table = table_entry["table"]
        direction = table_entry["direction"]
        fields = table_entry["fields"]
        extra_remote = table_entry.get("extra_remote", [])

        lines.append(f"### {table}  `{direction}`")
        lines.append("")
        lines.append("| Campo | Tipo | Categoría | Acción |")
        lines.append("|---|---|---|---|")
        for f in fields:
            lines.append(
                f"| {f['field']} | `{f['type']}` | {f['category']} | {f['action']} |"
            )
        for f in extra_remote:
            lines.append(
                f"| {f['field']} | `{f['type']}` | **{f['category']}** | {f['action']} |"
            )
        lines.append("")

    lines.extend([
        "## Campos extra en Airtable — DEPRECATED_FISCAL",
        "",
        "Estos campos **existen en Airtable** pero **no están** en `kanpai_airtable_schema.v1.json`.",
        "El drift checker los reporta como `CAMPO EXTRA`. Son el remanente del flujo fiscal",
        "retirado. No los elimines sin confirmar que no hay formularios, vistas ni automations",
        "que los usen.",
        "",
        "| Tabla | Campo | Motivo |",
        "|---|---|---|",
    ])
    deprecated = audit_result["deprecated_fiscal"]
    for table, fields_dict in sorted(deprecated.items()):
        for field_name, reason in sorted(fields_dict.items()):
            lines.append(f"| {table} | `{field_name}` | {reason} |")

    lines.extend([
        "",
        "### Cómo eliminar un campo en Airtable",
        "",
        "1. Verificar que ninguna automation, fórmula, vista ni interfaz referencia el campo.",
        "2. Hacer backup del reporte de drift actual.",
        "3. Eliminar el campo desde la UI de Airtable (campo → Opciones → Eliminar campo).",
        "4. Ejecutar `uv run python airtable/scripts/check_airtable_drift.py`.",
        "5. Verificar que el drift queda en 0 warnings relacionados con ese campo.",
        "",
    ])

    return "\n".join(lines)


def _fetch_remote_extra(
    base_id: str, token: str, schema: dict[str, Any]
) -> dict[str, list[str]]:
    """Fetch live Airtable schema and return fields not in local schema, per table."""
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    import time

    local_fields_by_table = {
        t["name"]: {f["name"] for f in t.get("fields", [])}
        for t in schema.get("tables", [])
    }

    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for attempt in range(1, 4):
        req = Request(url, headers=headers, method="GET")
        try:
            with urlopen(req, timeout=30) as response:  # noqa: S310
                remote_schema = json.loads(response.read().decode("utf-8"))
            break
        except (HTTPError, URLError) as error:
            if attempt < 3:
                time.sleep(min(2 ** attempt, 10))
                continue
            raise SystemExit(f"ERROR: no se pudo obtener schema remoto: {error}") from error

    extra: dict[str, list[str]] = {}
    for remote_table in remote_schema.get("tables", []):
        table_name = remote_table["name"]
        local_fields = local_fields_by_table.get(table_name, set())
        remote_fields = {f["name"] for f in remote_table.get("fields", [])}
        extra_fields = sorted(
            f for f in remote_fields - local_fields
            if remote_table["fields"][
                next(i for i, x in enumerate(remote_table["fields"]) if x["name"] == f)
            ].get("type") != "multipleRecordLinks"  # skip auto-backlinks
        )
        if extra_fields:
            extra[table_name] = extra_fields
    return extra


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify Airtable columns for audit and cleanup planning."
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Fetch live Airtable schema to discover fields not in local schema.",
    )
    parser.add_argument("--field-map", type=Path, default=DEFAULT_FIELD_MAP)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        field_map = _read_json(args.field_map)
        schema = _read_json(args.schema)
    except OSError as error:
        print(f"ERROR: no se pudo leer archivo local: {error}", file=sys.stderr)
        return 1

    extra_remote: dict[str, list[str]] | None = None
    if args.remote:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("AIRTABLE_API_TOKEN", "").strip()
        base_id = os.getenv("AIRTABLE_BASE_ID", "").strip()
        if not token or not base_id:
            print("ERROR: AIRTABLE_API_TOKEN y AIRTABLE_BASE_ID son necesarios con --remote.", file=sys.stderr)
            return 1
        print("Consultando schema remoto de Airtable...")
        extra_remote = _fetch_remote_extra(base_id, token, schema)

    result = audit(schema, field_map, extra_remote_fields=extra_remote)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    report_text = render_report(result)
    args.report.write_text(report_text, encoding="utf-8")

    totals = result["totals"]
    print("=== AUDITORÍA DE COLUMNAS AIRTABLE ===")
    for cat, count in sorted(totals.items()):
        print(f"  {cat}: {count}")
    total_extra = totals.get("EXTRA_LOCAL", 0) + totals.get("EXTRA_REMOTO", 0)
    deprecated_count = sum(len(v) for v in DEPRECATED_FISCAL.values())
    print(f"\n  EXTRA_LOCAL + EXTRA_REMOTO: {total_extra} (candidatos a revisar)")
    print(f"  DEPRECATED_FISCAL (en Airtable, no en schema): {deprecated_count}")
    print(f"\nReporte: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
