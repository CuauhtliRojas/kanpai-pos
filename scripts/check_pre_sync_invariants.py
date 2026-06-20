"""Read-only command line preflight for the local-first backend."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.services.preflight_service import run_local_backend_preflight  # noqa: E402


def main() -> int:
    """Print all local checks and return one only for critical errors."""
    with SessionLocal() as db:
        result = run_local_backend_preflight(db)

    print(f'PRE-SYNC PREFLIGHT: {result["status"]}')
    print(f'Database: {result["database"]}')
    for check in result["checks"]:
        print(f'[{check["status"]:7}] {check["key"]}: {check["message"]}')
    print("Summary:")
    for key, value in result["summary"].items():
        print(f"  {key}: {value}")
    return 1 if result["status"] == "ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
