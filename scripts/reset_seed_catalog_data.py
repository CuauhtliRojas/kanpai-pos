"""Controlled archival/reset of local seed catalog data."""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal, engine  # noqa: E402
from app.db.seed import (  # noqa: E402
    run_seed,
)
from app.models import (  # noqa: E402
    DiningTable,
    Employee,
    InventoryItem,
    Product,
    ProductionStation,
)
from scripts.reset_operational_data import reset_operational_data  # noqa: E402

CONFIRMATION = "RESET_SQLITE_CATALOG_REAL_SEED"
BACKUP_DIR = Path("data/backups")


def catalog_counts(db: Session) -> dict[str, int]:
    return {
        "products_active": int(db.scalar(select(func.count(Product.id)).where(Product.active.is_(True))) or 0),
        "inventory_items_active": int(db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.active.is_(True))) or 0),
        "stations_active": int(db.scalar(select(func.count(ProductionStation.id)).where(ProductionStation.active.is_(True))) or 0),
        "tables_active": int(db.scalar(select(func.count(DiningTable.id)).where(DiningTable.active.is_(True))) or 0),
        "employees_active": int(db.scalar(select(func.count(Employee.id)).where(Employee.active.is_(True))) or 0),
    }


def reset_seed_catalog_data(
    db: Session,
    *,
    dry_run: bool = True,
    confirmation: str | None = None,
    include_operational: bool = False,
) -> dict[str, dict[str, int]]:
    before = catalog_counts(db)
    if dry_run:
        return {"before": before, "after": before.copy()}
    if confirmation != CONFIRMATION:
        raise ValueError(f"Se requiere confirmación literal: {CONFIRMATION}")
    if include_operational:
        reset_operational_data(db)

    # Archive old catalog rows. Operational foreign keys remain valid.
    db.query(Product).update({Product.active: False, Product.visible_pos: False})
    db.query(InventoryItem).update({InventoryItem.active: False})
    db.query(ProductionStation).update({ProductionStation.active: False})
    db.query(DiningTable).update({DiningTable.active: False})
    db.query(Employee).update({Employee.active: False})
    db.commit()

    # Reuse the single canonical seed pipeline in a separate transaction.
    run_seed(include_development_data=False)
    db.expire_all()
    return {"before": before, "after": catalog_counts(db)}


def backup_database() -> Path:
    database = engine.url.database
    if not database:
        raise RuntimeError("La URL SQLite no contiene una ruta de base de datos.")
    source = Path(database).resolve()
    if not source.exists():
        raise FileNotFoundError(source)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"kanpai_pos_before_real_seed_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(source, target)
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--include-operational", action="store_true")
    args = parser.parse_args()
    dry_run = args.dry_run or args.confirm is None
    backup = None if dry_run else backup_database()
    with SessionLocal() as db:
        result = reset_seed_catalog_data(
            db,
            dry_run=dry_run,
            confirmation=args.confirm,
            include_operational=args.include_operational,
        )
    print(f"Modo: {'DRY-RUN' if dry_run else 'APLICADO'}")
    if backup:
        print(f"Backup: {backup}")
    print(f"Antes: {result['before']}")
    print(f"Después: {result['after']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
