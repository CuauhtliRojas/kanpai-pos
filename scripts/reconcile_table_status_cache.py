"""Report or repair table status cache from active ticket truth without deletes."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.domain.constants import TableStatus, TicketStatus  # noqa: E402
from app.models import DiningTable, Ticket  # noqa: E402

CONFIRMATION = "RECONCILE_TABLE_STATUS_CACHE"


def reconcile_table_status_cache(*, execute: bool, confirmation: str = "") -> list[dict]:
    if execute and confirmation != CONFIRMATION:
        raise ValueError(f"Para ejecutar usa --confirm {CONFIRMATION}")

    changes: list[dict] = []
    with SessionLocal() as db:
        active_tickets = list(
            db.scalars(
                select(Ticket)
                .where(Ticket.status.in_((TicketStatus.OPEN, TicketStatus.IN_PAYMENT)))
                .order_by(Ticket.table_id, Ticket.id.desc())
            )
        )
        by_table: dict[int, Ticket] = {}
        for ticket in active_tickets:
            by_table.setdefault(ticket.table_id, ticket)

        for table in db.scalars(select(DiningTable).order_by(DiningTable.id)):
            ticket = by_table.get(table.id)
            expected = (
                TableStatus.IN_PAYMENT
                if ticket and ticket.status == TicketStatus.IN_PAYMENT
                else TableStatus.OCCUPIED
                if ticket
                else TableStatus.FREE
            )
            if table.status_cache == expected:
                continue
            changes.append(
                {
                    "table_id": table.id,
                    "table": table.display_name,
                    "before": table.status_cache,
                    "after": expected,
                    "ticket": ticket.folio if ticket else None,
                }
            )
            if execute:
                table.status_cache = expected

        if execute:
            db.commit()
        else:
            db.rollback()
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    changes = reconcile_table_status_cache(
        execute=args.execute, confirmation=args.confirm
    )
    print(f"MODE: {'execute' if args.execute else 'dry-run'}")
    for item in changes:
        print(
            f"{item['table']}: {item['before']} -> {item['after']} "
            f"ticket={item['ticket'] or '-'}"
        )
    print(f"Cambios: {len(changes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
