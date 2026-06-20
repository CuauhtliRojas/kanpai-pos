"""Support inventory receipts, decimal movements, and local stock alerts.

Revision ID: d8b54f902a11
Revises: c31a6b9e2d47
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8b54f902a11"
down_revision: str | Sequence[str] | None = "c31a6b9e2d47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add phase 3-H fields and decimal precision required by conversions."""
    with op.batch_alter_table("unit_conversions") as batch_op:
        batch_op.alter_column(
            "factor",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )

    with op.batch_alter_table("purchase_receipts") as batch_op:
        batch_op.add_column(sa.Column("supplier_name", sa.String(160), nullable=True))
        batch_op.add_column(sa.Column("invoice_reference", sa.String(120), nullable=True))
        batch_op.add_column(sa.Column("note", sa.Text(), nullable=True))

    with op.batch_alter_table("purchase_receipt_lines") as batch_op:
        batch_op.alter_column(
            "captured_quantity",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "converted_quantity_base",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )

    with op.batch_alter_table("inventory_movements") as batch_op:
        batch_op.alter_column(
            "quantity_base",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "signed_quantity_base",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )
        batch_op.add_column(sa.Column("source_type", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("source_id", sa.Integer(), nullable=True))

    with op.batch_alter_table("stock_alerts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "threshold_quantity",
                sa.Numeric(18, 6),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "current_quantity",
                sa.Numeric(18, 6),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column("message", sa.Text(), nullable=False, server_default="")
        )


def downgrade() -> None:
    """Remove phase 3-H fields and restore integer quantity storage."""
    with op.batch_alter_table("stock_alerts") as batch_op:
        batch_op.drop_column("message")
        batch_op.drop_column("current_quantity")
        batch_op.drop_column("threshold_quantity")

    with op.batch_alter_table("inventory_movements") as batch_op:
        batch_op.drop_column("source_id")
        batch_op.drop_column("source_type")
        batch_op.alter_column(
            "signed_quantity_base",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "quantity_base",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("purchase_receipt_lines") as batch_op:
        batch_op.alter_column(
            "converted_quantity_base",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "captured_quantity",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("purchase_receipts") as batch_op:
        batch_op.drop_column("note")
        batch_op.drop_column("invoice_reference")
        batch_op.drop_column("supplier_name")

    with op.batch_alter_table("unit_conversions") as batch_op:
        batch_op.alter_column(
            "factor",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )
