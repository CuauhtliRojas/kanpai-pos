"""Add full recipe schema for preparations and variant options."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "rec01_full_recipe_schema"
down_revision = "d10preset001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "preparaciones_inventario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("codigo_preparacion", sa.String(length=80), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("insumo_resultante_id", sa.Integer(), nullable=False),
        sa.Column("rendimiento_cantidad_base", sa.Numeric(18, 6), nullable=False),
        sa.Column("unidad_resultado_id", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("airtable_registro_id", sa.String(length=64), nullable=True),
        sa.Column("remoto_revision", sa.String(length=128), nullable=True),
        sa.Column("remoto_actualizacion_fecha", sa.DateTime(), nullable=True),
        sa.Column("ultimo_descarga_fecha", sa.DateTime(), nullable=True),
        sa.Column("estado_sincronizacion", sa.String(length=32), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["insumo_resultante_id"], ["insumos_inventario.id"]),
        sa.ForeignKeyConstraint(["unidad_resultado_id"], ["unidades.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codigo_preparacion", name="uq_inventory_preparation_code"),
        sa.UniqueConstraint("airtable_registro_id"),
    )

    op.create_table(
        "recetas_preparacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("preparacion_id", sa.Integer(), nullable=False),
        sa.Column("inventario_insumo_id", sa.Integer(), nullable=False),
        sa.Column("cantidad_base", sa.Numeric(18, 6), nullable=False),
        sa.Column("porcentaje_merma", sa.Numeric(18, 6), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("airtable_registro_id", sa.String(length=64), nullable=True),
        sa.Column("remoto_revision", sa.String(length=128), nullable=True),
        sa.Column("remoto_actualizacion_fecha", sa.DateTime(), nullable=True),
        sa.Column("ultimo_descarga_fecha", sa.DateTime(), nullable=True),
        sa.Column("estado_sincronizacion", sa.String(length=32), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["inventario_insumo_id"], ["insumos_inventario.id"]),
        sa.ForeignKeyConstraint(["preparacion_id"], ["preparaciones_inventario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "preparacion_id",
            "inventario_insumo_id",
            name="uq_preparation_inventory_recipe",
        ),
        sa.UniqueConstraint("airtable_registro_id"),
    )

    op.create_table(
        "recetas_opcion_variante",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("opcion_variante_id", sa.Integer(), nullable=False),
        sa.Column("inventario_insumo_id", sa.Integer(), nullable=False),
        sa.Column("cantidad_base", sa.Numeric(18, 6), nullable=False),
        sa.Column("porcentaje_merma", sa.Numeric(18, 6), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("airtable_registro_id", sa.String(length=64), nullable=True),
        sa.Column("remoto_revision", sa.String(length=128), nullable=True),
        sa.Column("remoto_actualizacion_fecha", sa.DateTime(), nullable=True),
        sa.Column("ultimo_descarga_fecha", sa.DateTime(), nullable=True),
        sa.Column("estado_sincronizacion", sa.String(length=32), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["inventario_insumo_id"], ["insumos_inventario.id"]),
        sa.ForeignKeyConstraint(["opcion_variante_id"], ["opciones_variante_producto.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "opcion_variante_id",
            "inventario_insumo_id",
            name="uq_variant_option_inventory_recipe",
        ),
        sa.UniqueConstraint("airtable_registro_id"),
    )


def downgrade() -> None:
    op.drop_table("recetas_opcion_variante")
    op.drop_table("recetas_preparacion")
    op.drop_table("preparaciones_inventario")
