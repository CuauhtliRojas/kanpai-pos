"""Explicit QA-only reset for transactional local data."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.domain.constants import TableStatus  # noqa: E402
from app.models import (  # noqa: E402
    AuditEvent,
    CashExpense,
    CashShift,
    CommandBatch,
    DiningTable,
    EmployeeSession,
    InventoryMovement,
    Payment,
    PrintJob,
    PurchaseReceipt,
    PurchaseReceiptLine,
    StationOrder,
    StationOrderLine,
    StockAlert,
    SmsNotification,
    TableStatusEvent,
    Ticket,
    TicketDiscount,
    TicketLine,
    TicketLineModification,
    TicketLineNote,
    TicketLineVariantSelection,
    TicketSplit,
    TicketSplitLine,
)

OPERATIONAL_MODELS = (
    SmsNotification,
    EmployeeSession,
    TicketLineModification,
    StockAlert,
    InventoryMovement,
    PurchaseReceiptLine,
    PurchaseReceipt,
    CashExpense,
    PrintJob,
    StationOrderLine,
    StationOrder,
    CommandBatch,
    AuditEvent,
    TableStatusEvent,
    TicketLineNote,
    TicketSplitLine,
    TicketLineVariantSelection,
    TicketLine,
    TicketDiscount,
    Payment,
    TicketSplit,
    Ticket,
    CashShift,
)


def reset_operational_data(db: Session) -> dict[str, int]:
    """Delete only QA transactions and release all dining tables atomically.

    Catalogs, recipes, permissions, logical printers and folio sequences are
    intentionally outside this list. The caller owns commit or rollback.
    """
    deleted: dict[str, int] = {}
    for model in OPERATIONAL_MODELS:
        result = db.execute(delete(model))
        deleted[model.__tablename__] = result.rowcount or 0
    db.execute(DiningTable.__table__.update().values(status_cache=TableStatus.FREE))
    return deleted


def main(argv: list[str] | None = None) -> int:
    """Require explicit confirmation before executing the transactional reset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirm deletion of local operational QA data.",
    )
    args = parser.parse_args(argv)
    if not args.yes:
        print(
            "WARNING: no data was deleted. Re-run with --yes to confirm the QA reset."
        )
        return 0

    with SessionLocal() as db:
        deleted = reset_operational_data(db)
        db.commit()
    print(f"Operational QA reset complete: {sum(deleted.values())} rows deleted.")
    print("All dining tables were returned to Libre. Catalogs were preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
