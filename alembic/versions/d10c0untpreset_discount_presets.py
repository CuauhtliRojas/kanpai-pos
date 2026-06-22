"""Create discount preset catalog.

Revision ID: d10preset001
Revises: b3realcatalog001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d10preset001"
down_revision: str | Sequence[str] | None = "b3realcatalog001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "descuentos_predeterminados",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clave_descuento", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("tipo_descuento", sa.String(length=32), nullable=False),
        sa.Column("monto_centavos", sa.Integer(), nullable=True),
        sa.Column("porcentaje_bps", sa.Integer(), nullable=True),
        sa.Column("motivo_sugerido", sa.String(length=240), nullable=True),
        sa.Column("requiere_autorizacion", sa.Boolean(), nullable=False),
        sa.Column("visible_pos", sa.Boolean(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("airtable_registro_id", sa.String(length=64), nullable=True),
        sa.Column("remoto_revision", sa.String(length=128), nullable=True),
        sa.Column("remoto_actualizacion_fecha", sa.DateTime(), nullable=True),
        sa.Column("ultimo_descarga_fecha", sa.DateTime(), nullable=True),
        sa.Column("estado_sincronizacion", sa.String(length=32), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(tipo_descuento = 'Monto' AND monto_centavos > 0 "
            "AND porcentaje_bps IS NULL) OR "
            "(tipo_descuento = 'Porcentaje' AND monto_centavos IS NULL "
            "AND porcentaje_bps > 0 AND porcentaje_bps <= 10000) OR "
            "(tipo_descuento = 'Cortesia' AND monto_centavos IS NULL "
            "AND porcentaje_bps = 10000)",
            name="ck_discount_preset_value",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("airtable_registro_id"),
        sa.UniqueConstraint("clave_descuento"),
    )


def downgrade() -> None:
    op.drop_table("descuentos_predeterminados")
