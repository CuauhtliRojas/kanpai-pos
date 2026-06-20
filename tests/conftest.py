"""Force every pytest process and child process onto an isolated SQLite DB."""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPERATIONAL_DATABASE = (ROOT / "data/kanpai_pos.db").resolve()
TEST_DATABASE_DIR = Path(tempfile.mkdtemp(prefix="kanpai-pos-pytest-"))
TEST_DATABASE = (TEST_DATABASE_DIR / "kanpai_pos_test.db").resolve()


def _digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


_OPERATIONAL_DIGEST_BEFORE = _digest(OPERATIONAL_DATABASE)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"
os.environ["KANPAI_TEST_DATABASE_PATH"] = str(TEST_DATABASE)


def _initialize_test_database() -> None:
    import app.models  # noqa: F401
    from app.core.database import Base, engine

    Base.metadata.create_all(engine)


_initialize_test_database()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail the run if any test bypassed SessionLocal and touched production data."""
    if _digest(OPERATIONAL_DATABASE) != _OPERATIONAL_DIGEST_BEFORE:
        reporter = session.config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line(
                f"ERROR: pytest modificó la DB operativa: {OPERATIONAL_DATABASE}",
                red=True,
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED

    database_module = sys.modules.get("app.core.database")
    if database_module is not None:
        database_module.engine.dispose()
    shutil.rmtree(TEST_DATABASE_DIR, ignore_errors=True)
