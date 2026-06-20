import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import engine
from app.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "sqlite"


def test_pytest_database_is_isolated_from_operational_database() -> None:
    operational = (Path(__file__).resolve().parents[1] / "data/kanpai_pos.db").resolve()
    configured = Path(engine.url.database).resolve()

    assert configured == Path(os.environ["KANPAI_TEST_DATABASE_PATH"]).resolve()
    assert configured != operational
