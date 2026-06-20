"""Add cash shift closing and expense detail fields.

Revision ID: c31a6b9e2d47
Revises: aec316b102f0
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c31a6b9e2d47"
down_revision: str | Sequence[str] | None = "aec316b102f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add persisted closing results and align expense optional fields."""
    with op.batch_alter_table("cash_shifts") as batch_op:
        batch_op.add_column(sa.Column("cash_difference_cents", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("closing_note", sa.Text(), nullable=True))

    with op.batch_alter_table("cash_expenses") as batch_op:
        batch_op.alter_column(
            "expense_type",
            new_column_name="category",
            existing_type=sa.String(length=32),
            existing_nullable=False,
            nullable=True,
        )
        batch_op.alter_column(
            "payment_method_id",
            existing_type=sa.Integer(),
            existing_nullable=False,
            nullable=True,
        )
        batch_op.add_column(sa.Column("note", sa.Text(), nullable=True))


def downgrade() -> None:
    """Restore the previous expense shape and remove closing results."""
    op.execute(
        sa.text(
            "UPDATE cash_expenses SET category = 'OTRO' "
            "WHERE category IS NULL"
        )
    )
    op.execute(
        sa.text(
            "UPDATE cash_expenses SET payment_method_id = "
            "(SELECT id FROM payment_methods WHERE method_key = 'CASH' LIMIT 1) "
            "WHERE payment_method_id IS NULL"
        )
    )
    with op.batch_alter_table("cash_expenses") as batch_op:
        batch_op.drop_column("note")
        batch_op.alter_column(
            "payment_method_id",
            existing_type=sa.Integer(),
            existing_nullable=True,
            nullable=False,
        )
        batch_op.alter_column(
            "category",
            new_column_name="expense_type",
            existing_type=sa.String(length=32),
            existing_nullable=True,
            nullable=False,
        )

    with op.batch_alter_table("cash_shifts") as batch_op:
        batch_op.drop_column("closing_note")
        batch_op.drop_column("cash_difference_cents")
