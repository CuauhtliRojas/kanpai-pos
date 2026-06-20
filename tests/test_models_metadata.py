from app.core.database import Base
from app.domain.database_contract import TABLE_NAMES
import app.models  # noqa: F401


def test_catalog_sync_operation_and_inventory_tables_are_registered() -> None:
    legacy_tables = {
        "audit_events",
        "authorizations",
        "business_settings",
        "cash_expenses",
        "cash_shifts",
        "command_batches",
        "dining_tables",
        "employees",
        "employee_roles",
        "folio_sequences",
        "inventory_items",
        "inventory_movements",
        "menu_categories",
        "payment_methods",
        "payments",
        "permissions",
        "pos_devices",
        "pos_sessions",
        "printers",
        "print_jobs",
        "products",
        "product_packages",
        "product_package_items",
        "product_recipes",
        "product_station_assignments",
        "production_stations",
        "purchase_receipt_lines",
        "purchase_receipts",
        "roles",
        "role_permissions",
        "service_zones",
        "station_orders",
        "station_order_lines",
        "stock_alerts",
        "sync_inbox",
        "sync_outbox",
        "sync_watermarks",
        "table_status_events",
        "ticket_discounts",
        "ticket_line_notes",
        "ticket_lines",
        "tickets",
        "unit_conversions",
        "units",
    }

    expected_tables = {TABLE_NAMES[name] for name in legacy_tables}
    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
