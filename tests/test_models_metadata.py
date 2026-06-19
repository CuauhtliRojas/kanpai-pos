from app.core.database import Base
import app.models  # noqa: F401


def test_catalog_sync_and_operation_tables_are_registered() -> None:
    expected_tables = {
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
        "roles",
        "role_permissions",
        "service_zones",
        "station_orders",
        "station_order_lines",
        "sync_inbox",
        "sync_outbox",
        "sync_watermarks",
        "table_status_events",
        "ticket_discounts",
        "ticket_line_notes",
        "ticket_lines",
        "tickets",
        "units",
    }

    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
