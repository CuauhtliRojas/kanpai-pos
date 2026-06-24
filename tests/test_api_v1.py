from fastapi.testclient import TestClient

from app.db.seed import run_seed
from app.core.config import get_settings
from app.api.security import SessionIdentity, require_session
from app.main import app
from tests.auth_helpers import auth_headers


client = TestClient(app)


def _admin_headers() -> dict[str, str]:
    run_seed(include_development_data=True)
    response = client.post(
        "/api/v1/auth/login-pin",
        json={"employee_code": "EMP-0001", "pin": get_settings().kanpai_admin_pin},
    )
    assert response.status_code == 200
    return {"X-Kanpai-Session": response.json()["session_token"]}


def test_api_v1_system_db() -> None:
    response = client.get("/api/v1/system/db", headers=_admin_headers())

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "sqlite"


def test_api_v1_seed_summary() -> None:
    run_seed(include_development_data=True)

    response = client.get("/api/v1/system/seed-summary", headers=_admin_headers())

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

    response = client.get("/api/v1/operations/tables", headers=auth_headers(client))

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 17


def test_operations_employee_detail_and_permissions_hide_pin_hash() -> None:
    run_seed(include_development_data=True)
    headers = _admin_headers()
    employees = client.get("/api/v1/operations/employees", headers=headers).json()
    employee_id = employees[0]["id"]

    detail = client.get(f"/api/v1/operations/employees/{employee_id}", headers=headers)
    permissions = client.get(
        f"/api/v1/operations/employees/{employee_id}/permissions", headers=headers
    )
    assert detail.status_code == permissions.status_code == 200
    assert "pin_hash" not in detail.text
    assert "pin_hash" not in permissions.text
    assert detail.json()["roles"]
    assert permissions.json()["permissions"]


def test_operations_roles_permissions_and_new_read_routes_are_in_openapi() -> None:
    run_seed(include_development_data=True)
    headers = _admin_headers()
    roles = client.get("/api/v1/operations/roles", headers=headers)
    permissions = client.get("/api/v1/operations/permissions", headers=headers)
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
        "/api/v1/printing/jobs/claim-next",
        "/api/v1/printing/jobs/{print_job_id}/printed",
        "/api/v1/printing/jobs/{print_job_id}/failed",
    }
    assert expected <= set(paths)


def test_security_boundary_routes_reject_missing_session_and_remain_in_openapi() -> None:
    protected = {
        "/api/v1/system/db",
        "/api/v1/system/seed-summary",
        "/api/v1/system/airtable-sync",
        "/api/v1/preflight/local-backend",
        "/api/v1/notifications/sms",
        "/api/v1/operations/tables",
        "/api/v1/operations/employees",
        "/api/v1/operations/roles",
        "/api/v1/operations/permissions",
        "/api/v1/reports/operational-summary",
        "/api/v1/audit/events",
        "/api/v1/printing/jobs/pending",
    }
    for path in protected:
        assert client.get(path).status_code == 401
    assert protected <= set(client.get("/openapi.json").json()["paths"])


def test_diagnostic_rejects_session_without_support_permission() -> None:
    app.dependency_overrides[require_session] = lambda: SessionIdentity(
        employee=None,  # type: ignore[arg-type]
        roles=frozenset(),
        permissions=frozenset(),
    )
    try:
        response = client.get(
            "/api/v1/preflight/local-backend",
            headers={"X-Kanpai-Session": "restricted-session"},
        )
    finally:
        app.dependency_overrides.pop(require_session, None)
    assert response.status_code == 403


def test_admin_read_and_support_boundaries_reject_session_without_permission() -> None:
    app.dependency_overrides[require_session] = lambda: SessionIdentity(
        employee=None,  # type: ignore[arg-type]
        roles=frozenset(),
        permissions=frozenset(),
    )
    try:
        assert (
            client.get(
                "/api/v1/reports/operational-summary",
                headers={"X-Kanpai-Session": "restricted-session"},
            ).status_code
            == 403
        )
        assert (
            client.get(
                "/api/v1/audit/events",
                headers={"X-Kanpai-Session": "restricted-session"},
            ).status_code
            == 403
        )
        assert (
            client.get(
                "/api/v1/system/airtable-sync",
                headers={"X-Kanpai-Session": "restricted-session"},
            ).status_code
            == 200
        )
        assert (
            client.post(
                "/api/v1/pos/cash-shifts/open",
                json={"employee_id": 1, "opening_cash_cents": 0},
                headers={"X-Kanpai-Session": "restricted-session"},
            ).status_code
            == 403
        )
    finally:
        app.dependency_overrides.pop(require_session, None)


def test_openapi_classifies_security_boundaries() -> None:
    document = client.get("/openapi.json").json()
    assert {"KanpaiSession", "KanpaiWorkerKey"} <= set(
        document["components"]["securitySchemes"]
    )
    worker_operation = document["paths"][
        "/api/v1/printing/jobs/claim-next"
    ]["post"]
    admin_operation = document["paths"]["/api/v1/system/db"]["get"]
    assert "worker-only" in worker_operation["tags"]
    assert "admin-support" in admin_operation["tags"]
