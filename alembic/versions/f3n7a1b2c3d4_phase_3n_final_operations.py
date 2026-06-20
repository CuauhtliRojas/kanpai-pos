"""Add local auth, variants, ticket splits and SMS notifications.

Revision ID: f3n7a1b2c3d4
Revises: b3f4c8d91a20
"""

import sqlalchemy as sa
from alembic import op

revision = "f3n7a1b2c3d4"
down_revision = "b3f4c8d91a20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("empleados") as batch:
        batch.add_column(sa.Column("hash_pin", sa.String(255)))
        batch.add_column(sa.Column("pin_activo", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("ultimo_acceso", sa.DateTime()))

    op.create_table(
        "sesiones_empleado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empleado_id", sa.Integer(), nullable=False),
        sa.Column("token_sesion", sa.String(128), nullable=False, unique=True),
        sa.Column("estado", sa.String(32), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("expiracion_fecha", sa.DateTime(), nullable=False),
        sa.Column("cierre_fecha", sa.DateTime()),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"]),
    )
    op.create_table(
        "grupos_variante_producto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("seleccion_minima", sa.Integer(), nullable=False),
        sa.Column("seleccion_maxima", sa.Integer(), nullable=False),
        sa.Column("requerido", sa.Boolean(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
    )
    op.create_table(
        "opciones_variante_producto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("grupo_variante_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer()),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("sku", sa.String(80)),
        sa.Column("diferencia_precio_centavos", sa.Integer(), nullable=False),
        sa.Column("estacion_id", sa.Integer()),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["grupo_variante_id"], ["grupos_variante_producto.id"]),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.ForeignKeyConstraint(["estacion_id"], ["estaciones_produccion.id"]),
    )
    op.create_table(
        "selecciones_variante_linea",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_linea_id", sa.Integer(), nullable=False),
        sa.Column("grupo_variante_id", sa.Integer(), nullable=False),
        sa.Column("opcion_variante_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("diferencia_precio_centavos_instantanea", sa.Integer(), nullable=False),
        sa.Column("nombre_instantanea", sa.String(160), nullable=False),
        sa.Column("sku_instantanea", sa.String(80)),
        sa.Column("estacion_id_instantanea", sa.Integer()),
        sa.ForeignKeyConstraint(["ticket_linea_id"], ["lineas_ticket.id"]),
        sa.ForeignKeyConstraint(["grupo_variante_id"], ["grupos_variante_producto.id"]),
        sa.ForeignKeyConstraint(["opcion_variante_id"], ["opciones_variante_producto.id"]),
    )
    op.create_table(
        "divisiones_ticket",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("tipo_division", sa.String(32), nullable=False),
        sa.Column("partes", sa.Integer()),
        sa.Column("numero_parte", sa.Integer()),
        sa.Column("importe_centavos", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(32), nullable=False),
        sa.Column("creacion_por_empleado_id", sa.Integer(), nullable=False),
        sa.Column("cierre_fecha", sa.DateTime()),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["creacion_por_empleado_id"], ["empleados.id"]),
    )
    op.create_table(
        "lineas_division_ticket",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("division_ticket_id", sa.Integer(), nullable=False),
        sa.Column("ticket_linea_id", sa.Integer(), nullable=False),
        sa.Column("importe_centavos", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["division_ticket_id"], ["divisiones_ticket.id"]),
        sa.ForeignKeyConstraint(["ticket_linea_id"], ["lineas_ticket.id"]),
    )
    with op.batch_alter_table("pagos") as batch:
        batch.add_column(sa.Column("division_ticket_id", sa.Integer()))
        batch.create_foreign_key("fk_pago_division_ticket", "divisiones_ticket", ["division_ticket_id"], ["id"])

    op.create_table(
        "canales_notificacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("clave_canal", sa.String(64), nullable=False, unique=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("actualizacion_fecha", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "notificaciones_sms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canal_id", sa.Integer()),
        sa.Column("alerta_stock_id", sa.Integer(), unique=True),
        sa.Column("empleado_id", sa.Integer()),
        sa.Column("msisdn", sa.String(32), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(32), nullable=False),
        sa.Column("modo_prueba", sa.Boolean(), nullable=False),
        sa.Column("respuesta_contenido", sa.Text()),
        sa.Column("error", sa.Text()),
        sa.Column("creacion_fecha", sa.DateTime(), nullable=False),
        sa.Column("envio_fecha", sa.DateTime()),
        sa.ForeignKeyConstraint(["canal_id"], ["canales_notificacion.id"]),
        sa.ForeignKeyConstraint(["alerta_stock_id"], ["alertas_stock.id"]),
        sa.ForeignKeyConstraint(["empleado_id"], ["empleados.id"]),
    )


def downgrade() -> None:
    op.drop_table("notificaciones_sms")
    op.drop_table("canales_notificacion")
    with op.batch_alter_table("pagos") as batch:
        batch.drop_constraint("fk_pago_division_ticket", type_="foreignkey")
        batch.drop_column("division_ticket_id")
    op.drop_table("lineas_division_ticket")
    op.drop_table("divisiones_ticket")
    op.drop_table("selecciones_variante_linea")
    op.drop_table("opciones_variante_producto")
    op.drop_table("grupos_variante_producto")
    op.drop_table("sesiones_empleado")
    with op.batch_alter_table("empleados") as batch:
        batch.drop_column("ultimo_acceso")
        batch.drop_column("pin_activo")
        batch.drop_column("hash_pin")
