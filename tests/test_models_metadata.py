from app.core.database import Base
import app.models  # noqa: F401


def test_catalog_and_sync_tables_are_registered() -> None:
    expected_tables = {
        "menu_categories",
        "production_stations",
        "products",
        "product_station_assignments",
        "product_packages",
        "product_package_items",
        "units",
        "inventory_items",
        "product_recipes",
        "employees",
        "roles",
        "permissions",
        "employee_roles",
        "role_permissions",
        "sync_inbox",
        "sync_outbox",
        "sync_watermarks",
    }

    assert expected_tables.issubset(set(Base.metadata.tables.keys()))
