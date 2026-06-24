from fastapi.testclient import TestClient

from app.core.config import get_settings


def auth_headers(
    client: TestClient,
    employee_code: str = "EMP-0001",
    pin: str | None = None,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login-pin",
        json={
            "employee_code": employee_code,
            "pin": pin or get_settings().kanpai_admin_pin,
        },
    )
    assert response.status_code == 200
    return {"X-Kanpai-Session": response.json()["session_token"]}
