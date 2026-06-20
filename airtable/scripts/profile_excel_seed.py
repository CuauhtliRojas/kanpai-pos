"""Profile the live seed Excel without reading or writing Airtable."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from build_airtable_seed import DEFAULT_EXCEL, DEFAULT_FIXED, BuildResult, build_seed

DEFAULT_REPORT = Path("airtable/reports/airtable_seed_profile_report.md")


def render_report(result: BuildResult, excel_path: Path) -> str:
    issue_counts = Counter(issue.code for issue in result.issues)
    lines = [
        "# Airtable seed Excel profile",
        "",
        f"Excel: `{excel_path}`",
        f"Presente: {result.excel_present}",
        "",
        "## Conteos",
        "",
    ]
    for name, value in result.stats.items():
        lines.append(f"- {name}: {value}")
    lines.extend(["", "## Valores raros y referencias", ""])
    for name, value in sorted(issue_counts.items()):
        lines.append(f"- {name}: {value}")
    if not issue_counts:
        lines.append("- (sin hallazgos)")
    lines.extend(["", "## Detalle", ""])
    for issue in result.issues:
        location = ""
        if issue.sheet:
            location = f" [{issue.sheet}"
            if issue.row is not None:
                location += f" fila {issue.row}"
            location += "]"
        lines.append(f"- {issue.level}/{issue.code}{location}: {issue.message}")
    if not result.issues:
        lines.append("- (sin hallazgos)")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    parser.add_argument("--fixed", type=Path, default=DEFAULT_FIXED)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_seed(args.excel, args.fixed)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(result, args.excel), encoding="utf-8")
    print("AIRTABLE EXCEL PROFILE")
    for name, value in result.stats.items():
        print(f"{name}: {value}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Errores: {len(result.errors)}")
    print(f"Reporte: {args.report}")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
