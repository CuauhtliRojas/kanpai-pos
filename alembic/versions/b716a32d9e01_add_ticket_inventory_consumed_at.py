"""Add idempotency marker for sales inventory consumption.

Revision ID: b716a32d9e01
Revises: d8b54f902a11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b716a32d9e01"
down_revision: str | Sequence[str] | None = "d8b54f902a11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the nullable idempotency marker to tickets."""
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.add_column(
            sa.Column("inventory_consumed_at", sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    """Remove the sales inventory idempotency marker."""
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.drop_column("inventory_consumed_at")
