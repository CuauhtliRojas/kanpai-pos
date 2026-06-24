"""Prepare the local SQLite database for the first real production shift.

This script is intentionally conservative:
- It does not talk to Airtable.
- It does not run migrations.
- It does not execute unless --execute and a literal confirmation are provided.
- It creates a SQLite backup before deleting operational data.
- It preserves catalogs, employees, roles, permissions, PIN hashes, products,
  recipes, inventory items, tables, printers, stations and configuration.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import func, inspect, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    AuditEvent,
    CashExpense,
    CashShift,
    DiningTable,
    Employee,
    EmployeeSession,
    FolioSequence,
    InventoryItem,
    InventoryMovement,
    Payment,
    PrintJob,
    Product,
    PurchaseReceipt,
    StockAlert,
    Ticket,
)
from scripts.reset_operational_data import reset_operational_data  # noqa: E402

try:
    from app.models import Authorization, PosSession  # type: ignore[attr-defined]  # noqa: E402
except ImportError:  # pragma: no cover
    Authorization = None  # type: ignore[assignment,misc]
    PosSession = None  # type: ignore[assignment,misc]


CONFIRMATION = "PREPARE_KANPAI_PRODUCTION_DB"
BACKUP_DIR = ROOT / "data" / "backups"

OPERATIONAL_FOLIOS = (
    "TICKET",
    "CORTE",
    "PAGO",
    "COMANDA",
    "MOVIMIENTO",
    "GASTO",
    "IMPRESION",
    "RECEPCION",
)


def _count(db: Session, model: Any) -> int:
    return int(db.scalar(select(func.count(model.id))) or 0)


def _safe_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _column_names(db: Session, table_name: str) -> set[str]:
    inspector = inspect(db.get_bind())
    return {column["name"] for column in inspector.get_columns(table_name)}


def _movement_inventory_item_column(db: Session) -> str:
    inspector = inspect(db.get_bind())

    for fk in inspector.get_foreign_keys("movimientos_inventario"):
        if fk.get("referred_table") == "insumos_inventario":
            constrained = fk.get("constrained_columns") or []
            if constrained:
                return str(constrained[0])

    movement_columns = _column_names(db, "movimientos_inventario")
    for candidate in (
        "insumo_id",
        "inventory_item_id",
        "insumo_inventario_id",
        "item_id",
    ):
        if candidate in movement_columns:
            return candidate

    raise RuntimeError(
        "No pude resolver la columna FK de movimientos_inventario hacia insumos_inventario."
    )


def _movement_signed_quantity_column(db: Session) -> str:
    movement_columns = _column_names(db, "movimientos_inventario")

    for candidate in (
        "con_signo_cantidad_base",
        "cantidad_base_con_signo",
        "signed_quantity_base",
        "quantity_base_signed",
        "quantity_delta_base",
        "delta_cantidad_base",
    ):
        if candidate in movement_columns:
            return candidate

    raise RuntimeError(
        "No pude resolver la columna de cantidad con signo en movimientos_inventario."
    )


def count_inventory_items_with_nonzero_stock(db: Session) -> int:
    """Count active inventory items whose ledger-calculated stock is not zero."""
    inspector = inspect(db.get_bind())
    tables = set(inspector.get_table_names())

    if "insumos_inventario" not in tables or "movimientos_inventario" not in tables:
        return 0

    item_fk = _movement_inventory_item_column(db)
    signed_quantity = _movement_signed_quantity_column(db)

    query = f"""
        SELECT COUNT(*)
        FROM (
            SELECT i.id
            FROM {_safe_ident("insumos_inventario")} AS i
            LEFT JOIN {_safe_ident("movimientos_inventario")} AS m
                ON m.{_safe_ident(item_fk)} = i.id
            WHERE COALESCE(i.activo, 1) = 1
            GROUP BY i.id
            HAVING COALESCE(SUM(m.{_safe_ident(signed_quantity)}), 0) <> 0
        ) AS stock_por_insumo
    """
    return int(db.execute(text(query)).scalar() or 0)


def database_file_path() -> Path:
    database = engine.url.database
    if not database:
        raise RuntimeError("La URL SQLite no contiene ruta de base de datos.")
    path = Path(database)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def backup_database() -> Path:
    source = database_file_path()
    if not source.exists():
        raise FileNotFoundError(f"No existe la base SQLite: {source}")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"kanpai_pos_before_production_reset_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(source, target)
    return target


def production_counts(db: Session) -> dict[str, int]:
    counts = {
        "cash_shifts": _count(db, CashShift),
        "tickets": _count(db, Ticket),
        "payments": _count(db, Payment),
        "cash_expenses": _count(db, CashExpense),
        "print_jobs": _count(db, PrintJob),
        "inventory_movements": _count(db, InventoryMovement),
        "inventory_items_with_nonzero_stock": count_inventory_items_with_nonzero_stock(db),
        "purchase_receipts": _count(db, PurchaseReceipt),
        "stock_alerts": _count(db, StockAlert),
        "audit_events": _count(db, AuditEvent),
        "employee_sessions": _count(db, EmployeeSession),
        "products": _count(db, Product),
        "inventory_items": _count(db, InventoryItem),
        "employees": _count(db, Employee),
        "active_tables": int(
            db.scalar(select(func.count(DiningTable.id)).where(DiningTable.active.is_(True)))
            or 0
        ),
    }

    if PosSession is not None:
        counts["pos_sessions"] = _count(db, PosSession)

    if Authorization is not None:
        counts["authorizations"] = _count(db, Authorization)

    return counts


def delete_extra_operational_rows(db: Session) -> dict[str, int]:
    deleted: dict[str, int] = {}

    if Authorization is not None:
        deleted["autorizaciones"] = int(db.query(Authorization).delete(synchronize_session=False))

    if PosSession is not None:
        deleted["sesiones_pos"] = int(db.query(PosSession).delete(synchronize_session=False))

    return deleted


def reset_operational_folios(db: Session) -> dict[str, int]:
    updated: dict[str, int] = {}

    for sequence in db.scalars(
        select(FolioSequence).where(FolioSequence.sequence_key.in_(OPERATIONAL_FOLIOS))
    ):
        sequence.next_number = 1
        updated[sequence.sequence_key] = 1

    return updated


def prepare_production_database(
    db: Session,
    *,
    reset_folios: bool = False,
) -> dict[str, object]:
    before = production_counts(db)

    deleted = reset_operational_data(db)
    deleted.update(delete_extra_operational_rows(db))

    folios = reset_operational_folios(db) if reset_folios else {}

    db.flush()
    after = production_counts(db)

    return {
        "before": before,
        "deleted": deleted,
        "folios_reset": folios,
        "after": after,
    }


def print_result(result: dict[str, object], backup: Path | None) -> None:
    if backup is not None:
        print(f"Backup: {backup}")

    print("Before:")
    for key, value in result["before"].items():  # type: ignore[union-attr]
        print(f"  {key}: {value}")

    print("Deleted:")
    for key, value in result["deleted"].items():  # type: ignore[union-attr]
        if value:
            print(f"  {key}: {value}")

    if result["folios_reset"]:
        print("Folio counters reset:")
        for key in result["folios_reset"]:  # type: ignore[union-attr]
            print(f"  {key}: 1")

    print("After:")
    for key, value in result["after"].items():  # type: ignore[union-attr]
        print(f"  {key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply the production reset. Without this flag only a preview is printed.",
    )
    parser.add_argument(
        "--confirm",
        help=f"Literal confirmation required for execute: {CONFIRMATION}",
    )
    parser.add_argument(
        "--reset-folios",
        action="store_true",
        help="Reset operational folio counters to 1 after deleting QA operations.",
    )
    args = parser.parse_args(argv)

    if args.execute and args.confirm != CONFIRMATION:
        raise SystemExit(f"Se requiere confirmación literal: {CONFIRMATION}")

    backup = backup_database() if args.execute else None

    with SessionLocal() as db:
        if args.execute:
            result = prepare_production_database(db, reset_folios=args.reset_folios)
            db.commit()
            print("PRODUCTION DATABASE RESET APPLIED")
        else:
            result = {
                "before": production_counts(db),
                "deleted": {},
                "folios_reset": {},
                "after": production_counts(db),
            }
            print("PREVIEW ONLY: no data was changed.")
            print(f"To execute: --execute --confirm {CONFIRMATION}")

        print_result(result, backup)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())