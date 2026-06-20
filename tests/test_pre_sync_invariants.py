from pathlib import Path

import pytest

from app.core.database import SessionLocal
from app.db.seed import run_seed
from scripts.check_pre_sync_invariants import main
from scripts.reset_operational_data import reset_operational_data


@pytest.fixture(autouse=True)
def clean_invariant_data() -> None:
    run_seed()
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
    yield
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()


def test_invariant_script_returns_zero_for_healthy_seed(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "PRE-SYNC PREFLIGHT: OK" in output
    assert "single_open_cash_shift" in output


def test_smoke_script_contains_main_backend_endpoints() -> None:
    script = Path("scripts/smoke_local_backend.ps1")
    assert script.is_file()
    content = script.read_text(encoding="utf-8")
    required_fragments = (
        "/health",
        "uv run pytest",
        "uv run ruff check .",
        "git diff --check",
        "python -m app.db.seed",
        "/api/v1/pos/cash-shifts/open",
        "/open-ticket",
        "/lines",
        "/send-round",
        "/start-payment",
        "/payments",
        "/inventory-movements",
        "/api/v1/printing/jobs/pending",
        "/api/v1/reports/operational-summary",
        "/api/v1/audit/tickets/",
        "/api/v1/preflight/local-backend",
        "SMOKE OK",
    )
    assert all(fragment in content for fragment in required_fragments)
