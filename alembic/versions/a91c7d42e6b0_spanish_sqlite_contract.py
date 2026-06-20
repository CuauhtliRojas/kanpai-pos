"""Translate the physical SQLite contract and persisted domain values.

Revision ID: a91c7d42e6b0
Revises: e4a91bc6d2f0
Create Date: 2026-06-19
"""

from collections.abc import Mapping

from alembic import op
import sqlalchemy as sa

from app.domain.constants import AUDIT_EVENT_VALUES
from app.domain.database_contract import TABLE_NAMES, physical_column_name


revision = "a91c7d42e6b0"
down_revision = "e4a91bc6d2f0"
branch_labels = None
depends_on = None


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _rename_tables(mapping: Mapping[str, str]) -> None:
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    for old, new in mapping.items():
        if old in existing and old != new:
            op.rename_table(old, new)


def _current_model_columns() -> dict[str, dict[str, str]]:
    # Import after Alembic is initialized. Keys are stable Python attributes;
    # names are the Spanish physical identifiers introduced by this revision.
    from app.core.database import Base
    import app.models  # noqa: F401

    return {
        table.name: {column.key: column.name for column in table.columns}
        for table in Base.metadata.tables.values()
    }


def _rename_columns_to_spanish() -> None:
    inspector = sa.inspect(op.get_bind())
    for table in inspector.get_table_names():
        if table not in TABLE_NAMES.values():
            continue
        for column in list(inspector.get_columns(table)):
            old = column["name"]
            new = physical_column_name(old)
            if old != new:
                op.alter_column(table, old, new_column_name=new)


def _rename_columns_to_english() -> None:
    inspector = sa.inspect(op.get_bind())
    model_columns = _current_model_columns()
    for table in inspector.get_table_names():
        if table not in model_columns:
            continue
        reverse = {physical: python for python, physical in model_columns[table].items()}
        for column in list(inspector.get_columns(table)):
            old = column["name"]
            new = reverse[old]
            if old != new:
                op.alter_column(table, old, new_column_name=new)


def _update_values(table: str, column: str, mapping: Mapping[str, str]) -> None:
    table_name = TABLE_NAMES[table]
    column_name = physical_column_name(column)
    for old, new in mapping.items():
        op.execute(
            sa.text(
                f"UPDATE {_quote(table_name)} SET {_quote(column_name)} = :new "
                f"WHERE {_quote(column_name)} = :old"
            ).bindparams(old=old, new=new)
        )


VALUE_MIGRATIONS = (
    ("dining_tables", "status_cache", {"FREE": "Libre", "OCCUPIED": "Ocupada", "IN_PAYMENT": "En cobro"}),
    ("pos_sessions", "status", {"OPEN": "Abierto", "CLOSED": "Cerrado"}),
    ("cash_shifts", "status", {"OPEN": "Abierto", "CLOSED": "Cerrado"}),
    ("tickets", "status", {"OPEN": "Abierto", "IN_PAYMENT": "En cobro", "PAID": "Cobrado", "CANCELLED": "Cancelado"}),
    ("tickets", "payment_status", {"UNPAID": "Sin pagar", "PAID": "Pagado", "CANCELLED": "Cancelado"}),
    ("ticket_lines", "status", {"CAPTURED": "Capturado", "ENVIADO_COMANDA": "Enviado a comanda", "IMPRESO": "Impreso", "CANCELLED": "Cancelado", "CANCELED": "Cancelado", "CANCELADO": "Cancelado"}),
    ("ticket_lines", "line_type", {"SIMPLE": "Simple", "PACKAGE_PARENT": "Paquete padre", "PACKAGE_COMPONENT": "Componente de paquete"}),
    ("ticket_lines", "price_mode", {"NORMAL": "Normal", "PACKAGE_PRICE": "Precio de paquete", "INCLUDED_IN_PACKAGE": "Incluido en paquete"}),
    ("command_batches", "batch_type", {"ORDER": "Pedido"}),
    ("station_orders", "status", {"QUEUED": "En cola"}),
    ("station_order_lines", "line_action", {"ADD": "Agregar"}),
    ("print_jobs", "job_type", {"COMANDA": "Comanda", "TICKET": "Ticket", "CORTE": "Corte", "CANCELACION_COMANDA": "Cancelacion comanda"}),
    ("print_jobs", "status", {"PENDING": "Pendiente", "CLAIMED": "Tomado", "PRINTED": "Impreso", "FAILED": "Fallido", "CANCELLED": "Cancelado"}),
    ("payments", "status", {"ACTIVE": "Activo", "CANCELLED": "Cancelado"}),
    ("cash_expenses", "status", {"ACTIVE": "Activo", "CANCELLED": "Cancelado"}),
    ("payment_methods", "method_key", {"CASH": "Efectivo", "CARD": "Tarjeta", "TRANSFER": "Transferencia"}),
    ("inventory_movements", "movement_type", {"PURCHASE": "Compra", "ADJUSTMENT_IN": "Ajuste entrada", "ADJUSTMENT_OUT": "Ajuste salida", "WASTE": "Merma", "SALE_CONSUMPTION": "Consumo venta"}),
    ("inventory_movements", "source_type", {"TICKET_LINE": "Linea ticket", "PACKAGE_COMPONENT": "Componente de paquete", "MANUAL": "Manual"}),
    ("stock_alerts", "alert_type", {"LOW_STOCK": "Stock bajo"}),
    ("stock_alerts", "status", {"OPEN": "Abierta", "RESOLVED": "Resuelta"}),
    ("purchase_receipts", "receipt_type", {"PURCHASE": "Compra"}),
    ("purchase_receipts", "status", {"DRAFT": "Borrador", "PROCESSED": "Procesada"}),
    ("purchase_receipt_lines", "status", {"PENDING": "Pendiente", "PROCESSED": "Procesada"}),
    ("products", "product_type", {"SIMPLE": "Simple", "PACKAGE": "Paquete"}),
    ("inventory_items", "item_type", {"OTRO": "Otro"}),
    ("units", "unit_family", {"MASS": "Masa", "VOLUME": "Volumen", "COUNT": "Conteo"}),
    ("product_packages", "package_mode", {"FIXED_COMPONENTS": "Componentes fijos"}),
    ("product_packages", "print_behavior", {"PRINT_COMPONENTS": "Imprimir componentes"}),
    ("product_packages", "inventory_behavior", {"CONSUME_COMPONENT_RECIPES": "Consumir recetas de componentes"}),
    ("printers", "connection_type", {"LOGICAL": "Logica"}),
    ("authorizations", "status", {"APPROVED": "Aprobada"}),
    ("sync_inbox", "status", {"PENDING": "Pendiente"}),
    ("sync_outbox", "status", {"PENDING": "Pendiente"}),
    ("sync_watermarks", "status", {"IDLE": "Inactivo"}),
    ("audit_events", "event_type", AUDIT_EVENT_VALUES),
)

SYNC_CATALOG_TABLES = (
    "menu_categories", "production_stations", "products",
    "product_station_assignments", "product_packages", "product_package_items",
    "units", "inventory_items", "product_recipes", "employees", "roles", "permissions",
)


def upgrade() -> None:
    _rename_tables(TABLE_NAMES)
    _rename_columns_to_spanish()
    for table, column, mapping in VALUE_MIGRATIONS:
        _update_values(table, column, mapping)
    for table in SYNC_CATALOG_TABLES:
        _update_values(table, "sync_status", {"ACTIVE": "Activo"})


def downgrade() -> None:
    for table in reversed(SYNC_CATALOG_TABLES):
        _update_values(table, "sync_status", {"Activo": "ACTIVE"})
    for table, column, mapping in reversed(VALUE_MIGRATIONS):
        _update_values(table, column, {value: key for key, value in mapping.items()})
    _rename_columns_to_english()
    _rename_tables({spanish: english for english, spanish in TABLE_NAMES.items()})
