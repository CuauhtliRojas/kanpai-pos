from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import uvicorn
from dotenv import load_dotenv


APP_ID = "mx.kanpai.pos"


def runtime_dir() -> Path:
    configured = os.getenv("KANPAI_RUNTIME_DIR")
    if configured:
        return Path(configured)

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_ID

    return Path.home() / f".{APP_ID}"


def bundle_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))

    return Path(__file__).resolve().parents[1]


def write_startup_trace(runtime: Path, message: str) -> None:
    logs_dir = runtime / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    trace_path = logs_dir / "startup-trace.log"
    timestamp = datetime.now().isoformat(timespec="seconds")
    with trace_path.open("a", encoding="utf-8") as file:
        file.write(f"{timestamp} {message}\n")


def configure_environment() -> Path:
    runtime = runtime_dir()
    data_dir = runtime / "data"
    media_dir = data_dir / "media" / "product-images"
    logs_dir = runtime / "logs"

    data_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    env_path = runtime / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)

    os.environ.setdefault("KANPAI_RUNTIME_DIR", str(runtime))
    os.environ.setdefault("KANPAI_DATA_DIR", str(data_dir))
    os.environ.setdefault("KANPAI_MEDIA_DIR", str(media_dir))
    os.environ.setdefault("KANPAI_LOG_DIR", str(logs_dir))

    db_path = data_dir / "kanpai_pos.db"
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    root = bundle_root()
    os.chdir(root)

    write_startup_trace(runtime, f"BUNDLE_ROOT={root}")
    write_startup_trace(runtime, f"ENV_PATH={env_path} exists={env_path.exists()}")
    write_startup_trace(runtime, f"DATABASE_URL={os.environ.get('DATABASE_URL')}")
    write_startup_trace(runtime, f"AIRTABLE_SYNC_ENABLED={os.environ.get('AIRTABLE_SYNC_ENABLED')}")
    write_startup_trace(runtime, f"AIRTABLE_SYNC_PULL_ENABLED={os.environ.get('AIRTABLE_SYNC_PULL_ENABLED')}")
    write_startup_trace(runtime, f"AIRTABLE_SYNC_PUSH_ENABLED={os.environ.get('AIRTABLE_SYNC_PUSH_ENABLED')}")
    write_startup_trace(runtime, f"FIELD_MAP_EXISTS={(root / 'airtable/schema/field_map.v1.json').exists()}")
    write_startup_trace(runtime, f"AIRTABLE_SCHEMA_EXISTS={(root / 'airtable/schema/kanpai_airtable_schema.v1.json').exists()}")
    write_startup_trace(runtime, f"PUSH_SCRIPT_EXISTS={(root / 'airtable/scripts/push_sqlite_to_airtable.py').exists()}")
    write_startup_trace(runtime, f"PULL_SCRIPT_EXISTS={(root / 'airtable/scripts/pull_airtable_to_sqlite.py').exists()}")

    return runtime


def main() -> None:
    runtime = configure_environment()

    port = int(os.getenv("KANPAI_API_PORT", "8000"))
    write_startup_trace(runtime, f"KANPAI_API_PORT={port}")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        log_config=None,
        access_log=False,
        use_colors=False,
    )


if __name__ == "__main__":
    main()
