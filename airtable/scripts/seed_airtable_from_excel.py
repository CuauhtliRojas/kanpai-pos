"""Idempotent, non-destructive seed pipeline for Airtable records."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from airtable_records_client import AirtableRecordsClient, AirtableRecordsError
from build_airtable_seed import (
    DEFAULT_EXCEL,
    DEFAULT_FIXED,
    LINK_FIELDS,
    NATURAL_KEYS,
    TABLE_ORDER,
    BuildResult,
    SeedIssue,
    build_seed,
)

CONFIRM_TEXT = "SEED_KANPAI_AIRTABLE"
DEFAULT_REPORT = Path("airtable/reports/airtable_seed_dry_run_report.md")


def dry_run_plan(
    client: AirtableRecordsClient | None,
    result: BuildResult,
    issues: list[SeedIssue],
) -> dict[str, dict[str, int]]:
    plan: dict[str, dict[str, int]] = {}
    for table in TABLE_ORDER:
        records = result.tables[table]
        keys = {str(record[NATURAL_KEYS[table]]).strip() for record in records}
        if client is None:
            plan[table] = {
                "creates": len(records),
                "updates": 0,
                "unchanged": 0,
                "upserts": len(records),
            }
            continue
        try:
            existing = client.index_by_key(table, NATURAL_KEYS[table])
        except AirtableRecordsError as error:
            issues.append(SeedIssue("error", "remote_read_failed", str(error)))
            plan[table] = {
                "creates": 0,
                "updates": 0,
                "unchanged": 0,
                "upserts": len(records),
            }
            continue
        existing_keys = set(existing)
        plan[table] = {
            "creates": len(keys - existing_keys),
            "updates": len(keys & existing_keys),
            "unchanged": 0,
            "upserts": len(records),
        }
    return plan


def resolve_links(
    table: str,
    records: list[dict[str, Any]],
    indexes: dict[str, dict[str, dict[str, Any]]],
    issues: list[SeedIssue],
) -> list[dict[str, Any]]:
    resolved_records = []
    for source in records:
        record = dict(source)
        skip_record = False
        for field, (target_table, _target_key) in LINK_FIELDS.get(table, {}).items():
            natural_values = record.get(field, [])
            ids = []
            missing = []
            for natural_value in natural_values:
                target = indexes.get(target_table, {}).get(str(natural_value).strip())
                if target:
                    ids.append(target["id"])
                else:
                    missing.append(str(natural_value))
            if missing:
                key = source.get(NATURAL_KEYS[table], "")
                issues.append(
                    SeedIssue(
                        "warning",
                        "unresolved_link",
                        f"{table}.{key}: {field} no resuelto en {target_table}: {', '.join(missing)}",
                    )
                )
                skip_record = True
                break
            record[field] = ids
        if not skip_record:
            resolved_records.append(record)
    return resolved_records


def execute_seed(
    client: AirtableRecordsClient,
    result: BuildResult,
    issues: list[SeedIssue],
) -> dict[str, dict[str, int]]:
    indexes: dict[str, dict[str, dict[str, Any]]] = {}
    summary: dict[str, dict[str, int]] = {}
    for table in TABLE_ORDER:
        resolved = resolve_links(table, result.tables[table], indexes, issues)
        outcome = client.upsert_by_key(table, NATURAL_KEYS[table], resolved)
        indexes[table] = outcome.pop("index")
        summary[table] = outcome
    return summary


def render_report(
    *,
    mode: str,
    result: BuildResult,
    issues: list[SeedIssue],
    summary: dict[str, dict[str, int]],
    remote_preview: bool,
) -> str:
    lines = [
        "# Airtable seed report",
        "",
        f"Modo: {mode}",
        f"Excel presente: {result.excel_present}",
        f"Preview remoto read-only: {remote_preview}",
        "",
        "## Resumen por tabla",
        "",
        "| Tabla | Creates | Updates | Unchanged | Upserts |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for table in TABLE_ORDER:
        item = summary.get(table, {})
        lines.append(
            f"| {table} | {item.get('created', item.get('creates', 0))} | "
            f"{item.get('updated', item.get('updates', 0))} | "
            f"{item.get('unchanged', 0)} | {item.get('upserts', len(result.tables[table]))} |"
        )
    lines.extend(["", "## Perfil Excel", ""])
    for name, value in result.stats.items():
        lines.append(f"- {name}: {value}")
    lines.extend(["", "## Warnings y errores", ""])
    for issue in issues:
        location = f" [{issue.sheet}:{issue.row}]" if issue.sheet else ""
        lines.append(f"- {issue.level}/{issue.code}{location}: {issue.message}")
    if not issues:
        lines.append("- (sin hallazgos)")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    parser.add_argument("--fixed", type=Path, default=DEFAULT_FIXED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Dry-run sin GET remoto; todos los upserts se muestran como creates potenciales.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.execute and args.dry_run:
        raise SystemExit("Usa --dry-run o --execute, no ambos.")
    if args.execute and args.confirm != CONFIRM_TEXT:
        raise SystemExit(f"Para ejecutar usa --execute --confirm {CONFIRM_TEXT}")

    result = build_seed(args.excel, args.fixed)
    issues = list(result.issues)
    mode = "execute" if args.execute else "dry-run"
    remote_preview = False

    if result.errors:
        summary: dict[str, dict[str, int]] = {}
    elif args.execute:
        try:
            client = AirtableRecordsClient.from_env()
            summary = execute_seed(client, result, issues)
        except AirtableRecordsError as error:
            issues.append(SeedIssue("error", "airtable_seed_failed", str(error)))
            summary = {}
    else:
        client = None
        if not args.offline:
            try:
                client = AirtableRecordsClient.from_env()
                remote_preview = True
            except AirtableRecordsError as error:
                issues.append(
                    SeedIssue(
                        "warning",
                        "remote_preview_unavailable",
                        f"{error} Se usa estimación offline.",
                    )
                )
        summary = dry_run_plan(client, result, issues)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_report(
            mode=mode,
            result=result,
            issues=issues,
            summary=summary,
            remote_preview=remote_preview,
        ),
        encoding="utf-8",
    )
    errors = [issue for issue in issues if issue.level == "error"]
    warnings = [issue for issue in issues if issue.level == "warning"]
    print(f"MODE: {mode}")
    for table in TABLE_ORDER:
        item = summary.get(table, {})
        creates = item.get("created", item.get("creates", 0))
        updates = item.get("updated", item.get("updates", 0))
        unchanged = item.get("unchanged", 0)
        print(f"{table}: creates={creates} updates={updates} unchanged={unchanged}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errores: {len(errors)}")
    print(f"Reporte: {args.report}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
