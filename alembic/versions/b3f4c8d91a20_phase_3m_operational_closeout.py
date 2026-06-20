"""Add production lifecycle, fiscal policy and operational traceability.

Revision ID: b3f4c8d91a20
Revises: a91c7d42e6b0
Create Date: 2026-06-19
"""

from alembic import op
import sqlalchemy as sa


revision = "b3f4c8d91a20"
down_revision = "a91c7d42e6b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("configuracion_negocio") as batch:
        batch.add_column(
            sa.Column("impuestos_activos", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch.add_column(
            sa.Column("tasa_impuesto_bps", sa.Integer(), nullable=False, server_default="1600")
        )
        batch.add_column(
            sa.Column("impuesto_incluido", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column("etiqueta_impuesto", sa.String(40), nullable=False, server_default="IVA")
        )

    with op.batch_alter_table("ordenes_estacion") as batch:
        # ``finished_at`` and ``completed_at`` share ``terminacion_fecha``.
        batch.add_column(sa.Column("recepcion_por_empleado_id", sa.Integer()))
        batch.add_column(sa.Column("inicio_por_empleado_id", sa.Integer()))
        batch.add_column(sa.Column("terminacion_por_empleado_id", sa.Integer()))
        batch.add_column(sa.Column("entrega_por_empleado_id", sa.Integer()))
        batch.create_foreign_key(
            "fk_orden_estacion_recepcion_empleado", "empleados", ["recepcion_por_empleado_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_orden_estacion_inicio_empleado", "empleados", ["inicio_por_empleado_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_orden_estacion_terminacion_empleado", "empleados", ["terminacion_por_empleado_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_orden_estacion_entrega_empleado", "empleados", ["entrega_por_empleado_id"], ["id"]
        )

    with op.batch_alter_table("descuentos_ticket") as batch:
        batch.add_column(sa.Column("porcentaje_bps", sa.Integer()))
        batch.add_column(
            sa.Column("es_cortesia", sa.Boolean(), nullable=False, server_default=sa.false())
        )

    op.create_table(
        "modificaciones_linea_ticket",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_linea_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("nota", sa.Text(), nullable=False),
        sa.Column("creacion_por_empleado_id", sa.Integer(), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("impresion_trabajo_id", sa.Integer()),
        sa.ForeignKeyConstraint(["ticket_linea_id"], ["lineas_ticket.id"]),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["creacion_por_empleado_id"], ["empleados.id"]),
        sa.ForeignKeyConstraint(["impresion_trabajo_id"], ["trabajos_impresion.id"]),
    )


def downgrade() -> None:
    op.drop_table("modificaciones_linea_ticket")
    with op.batch_alter_table("descuentos_ticket") as batch:
        batch.drop_column("es_cortesia")
        batch.drop_column("porcentaje_bps")
    with op.batch_alter_table("ordenes_estacion") as batch:
        batch.drop_constraint("fk_orden_estacion_entrega_empleado", type_="foreignkey")
        batch.drop_constraint("fk_orden_estacion_terminacion_empleado", type_="foreignkey")
        batch.drop_constraint("fk_orden_estacion_inicio_empleado", type_="foreignkey")
        batch.drop_constraint("fk_orden_estacion_recepcion_empleado", type_="foreignkey")
        batch.drop_column("entrega_por_empleado_id")
        batch.drop_column("terminacion_por_empleado_id")
        batch.drop_column("inicio_por_empleado_id")
        batch.drop_column("recepcion_por_empleado_id")
    with op.batch_alter_table("configuracion_negocio") as batch:
        batch.drop_column("etiqueta_impuesto")
        batch.drop_column("impuesto_incluido")
        batch.drop_column("tasa_impuesto_bps")
        batch.drop_column("impuestos_activos")
