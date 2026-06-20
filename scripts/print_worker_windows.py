"""Daemon local que consume la cola API e imprime snapshots en Windows."""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

HttpPost = Callable[[str, dict], dict]


def configure_logging() -> None:
    """Configura log persistente y consola sin depender del directorio actual."""
    log_dir = Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_dir / "print_worker.log", encoding="utf-8"), logging.StreamHandler()],
    )


def post_json(url: str, payload: dict) -> dict:
    """Envía JSON al backend con timeout para no bloquear el ciclo completo."""
    request = Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=10) as response:  # noqa: S310 - URL local configurada por operador
        return json.loads(response.read().decode())


def print_windows(printer_name: str, content: str) -> None:
    """Imprime texto RAW mediante pywin32, requerido solo en la estación Windows."""
    try:
        import win32print
    except ImportError as error:
        raise RuntimeError("pywin32 no está instalado; use --dry-run o instálelo en el entorno del worker.") from error
    handle = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(handle, 1, ("Kanpai POS", None, "RAW"))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, (content + "\n\n\n").encode("cp858", errors="replace"))
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)


def process_once(config: dict, *, dry_run: bool = False, http_post: HttpPost = post_json, printer: Callable[[str, str], None] = print_windows) -> int:
    """Procesa como máximo un trabajo por clave y confirma siempre su resultado."""
    base = config["api_base_url"].rstrip("/")
    worker_id = config["worker_id"]
    processed = 0
    for printer_key, windows_name in config["printers"].items():
        claimed = http_post(f"{base}/api/v1/printing/jobs/claim-next", {"printer_key": printer_key, "worker_id": worker_id})
        job = claimed.get("job")
        if not job:
            continue
        processed += 1
        try:
            if dry_run:
                logging.info("DRY-RUN job=%s printer=%s content=%r", job["id"], windows_name, job["content_snapshot"])
            else:
                printer(windows_name, job["content_snapshot"])
            http_post(f"{base}/api/v1/printing/jobs/{job['id']}/printed", {"worker_id": worker_id})
        except Exception as error:
            logging.exception("Falló job=%s printer=%s", job["id"], windows_name)
            http_post(
                f"{base}/api/v1/printing/jobs/{job['id']}/failed",
                {"worker_id": worker_id, "error_message": str(error)[:1000]},
            )
    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker físico de impresión Kanpai POS para Windows")
    parser.add_argument("--config", default=str(Path(__file__).with_name("print_worker_config.json")))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    configure_logging()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    while True:
        try:
            process_once(config, dry_run=args.dry_run)
        except Exception:
            logging.exception("Error de comunicación en ciclo del worker")
        if args.once:
            return
        time.sleep(max(float(config.get("poll_seconds", 2)), 0.2))


if __name__ == "__main__":
    main()
