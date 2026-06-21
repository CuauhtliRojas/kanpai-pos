from fastapi.testclient import TestClient

from app.db.seed import run_seed
from app.main import app


client = TestClient(app)


def test_api_v1_system_db() -> None:
    response = client.get("/api/v1/system/db")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "sqlite"


def test_api_v1_seed_summary() -> None:
    run_seed(include_development_data=True)

    response = client.get("/api/v1/system/seed-summary")

    assert response.status_code == 200
    payload = response.json()

    assert payload["business_settings"] == 1
    assert payload["tables"] >= 20
    assert payload["categories"] >= 1
    assert payload["stations"] >= 1
    assert payload["payment_methods"] >= 3
    assert payload["employees"] >= 1


def test_api_v1_catalog_categories() -> None:
    run_seed(include_development_data=True)

    response = client.get("/api/v1/catalog/categories")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_api_v1_catalog_stations() -> None:
    run_seed(include_development_data=True)

    response = client.get("/api/v1/catalog/stations")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_api_v1_catalog_products() -> None:
    run_seed(include_development_data=True)

    response = client.get("/api/v1/catalog/products")

    assert response.status_code == 200
    products = response.json()
    assert {"DEV-CHELA", "DEV-SAKE", "DEV-CHELA-SAKE"} <= {
        product["sku"] for product in products
    }


def test_api_v1_operations_tables() -> None:
    run_seed(include_development_data=True)

    response = client.get("/api/v1/operations/tables")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 17


def test_operations_employee_detail_and_permissions_hide_pin_hash() -> None:
    run_seed(include_development_data=True)
    employees = client.get("/api/v1/operations/employees").json()
    employee_id = employees[0]["id"]

    detail = client.get(f"/api/v1/operations/employees/{employee_id}")
    permissions = client.get(
        f"/api/v1/operations/employees/{employee_id}/permissions"
    )
    assert detail.status_code == permissions.status_code == 200
    assert "pin_hash" not in detail.text
    assert "pin_hash" not in permissions.text
    assert detail.json()["roles"]
    assert permissions.json()["permissions"]


def test_operations_roles_permissions_and_new_read_routes_are_in_openapi() -> None:
    run_seed(include_development_data=True)
    roles = client.get("/api/v1/operations/roles")
    permissions = client.get("/api/v1/operations/permissions")
    assert roles.status_code == permissions.status_code == 200
    assert any(role["role_key"] == "ADMIN" for role in roles.json())
    assert any(
        permission["permission_key"] == "INVENTORY_ADJUST"
        for permission in permissions.json()
    )

    paths = client.get("/openapi.json").json()["paths"]
    expected = {
        "/api/v1/reports/sales-by-category",
        "/api/v1/inventory/movements",
        "/api/v1/printing/jobs",
        "/api/v1/printing/printers",
        "/api/v1/operations/employees/{employee_id}",
        "/api/v1/operations/employees/{employee_id}/permissions",
        "/api/v1/operations/roles",
        "/api/v1/operations/permissions",
    }
    assert expected <= set(paths)
