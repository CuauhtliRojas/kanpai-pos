"""Use fixed precision for inventory minimums and product recipes.

Revision ID: c4d8e2f1a6b9
Revises: f3n7a1b2c3d4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4d8e2f1a6b9"
down_revision: str | Sequence[str] | None = "f3n7a1b2c3d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Preserve existing integers while enabling six decimal places."""
    with op.batch_alter_table("insumos_inventario") as batch_op:
        batch_op.alter_column(
            "minimo_stock_cantidad",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )

    with op.batch_alter_table("recetas_producto") as batch_op:
        batch_op.alter_column(
            "cantidad_base",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "porcentaje_merma",
            existing_type=sa.Integer(),
            type_=sa.Numeric(18, 6),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Restore INTEGER only when every persisted quantity is integral."""
    connection = op.get_bind()
    non_integral_minimums = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM insumos_inventario "
            "WHERE minimo_stock_cantidad != CAST(minimo_stock_cantidad AS INTEGER)"
        )
    )
    non_integral_recipes = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM recetas_producto "
            "WHERE cantidad_base != CAST(cantidad_base AS INTEGER)"
        )
    )
    non_integral_waste = connection.scalar(
        sa.text(
            "SELECT COUNT(*) FROM recetas_producto "
            "WHERE porcentaje_merma != CAST(porcentaje_merma AS INTEGER)"
        )
    )
    if non_integral_minimums or non_integral_recipes or non_integral_waste:
        raise RuntimeError(
            "Downgrade bloqueado: existen cantidades decimales que INTEGER truncaría."
        )

    with op.batch_alter_table("recetas_producto") as batch_op:
        batch_op.alter_column(
            "porcentaje_merma",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "cantidad_base",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("insumos_inventario") as batch_op:
        batch_op.alter_column(
            "minimo_stock_cantidad",
            existing_type=sa.Numeric(18, 6),
            type_=sa.Integer(),
            existing_nullable=False,
        )
