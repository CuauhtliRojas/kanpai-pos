"""Add operational claim and retry fields to print jobs.

Revision ID: e4a91bc6d2f0
Revises: b716a32d9e01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4a91bc6d2f0"
down_revision: str | Sequence[str] | None = "b716a32d9e01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add worker ownership, failure timing, and retry scheduling fields."""
    with op.batch_alter_table("print_jobs") as batch_op:
        batch_op.add_column(sa.Column("claimed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("claimed_by", sa.String(160), nullable=True))
        batch_op.add_column(sa.Column("failed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("next_retry_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove operational queue fields while preserving existing print data."""
    with op.batch_alter_table("print_jobs") as batch_op:
        batch_op.drop_column("next_retry_at")
        batch_op.drop_column("failed_at")
        batch_op.drop_column("claimed_by")
        batch_op.drop_column("claimed_at")
