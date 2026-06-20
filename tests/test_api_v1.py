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
    run_seed()

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
    run_seed()

    response = client.get("/api/v1/catalog/categories")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_api_v1_catalog_stations() -> None:
    run_seed()

    response = client.get("/api/v1/catalog/stations")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_api_v1_catalog_products() -> None:
    run_seed()

    response = client.get("/api/v1/catalog/products")

    assert response.status_code == 200
    products = response.json()
    assert {"DEV-CHELA", "DEV-SAKE", "DEV-CHELA-SAKE"} <= {
        product["sku"] for product in products
    }


def test_api_v1_operations_tables() -> None:
    run_seed()

    response = client.get("/api/v1/operations/tables")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 20
