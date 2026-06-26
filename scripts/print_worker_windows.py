"""Daemon local que consume la cola API e imprime snapshots en Windows."""

import argparse
import ctypes
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable
from urllib.request import Request, urlopen
from ctypes import wintypes

PrinterTarget = str | dict[str, Any]
HttpPost = Callable[[str, dict, str | None], dict]
Printer = Callable[[PrinterTarget, str], None]


def app_base_dir() -> Path:
    """Devuelve la carpeta base del repo en dev o del EXE en modo empaquetado."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    """Devuelve el config por defecto segun modo script o EXE."""
    if getattr(sys, "frozen", False):
        return app_base_dir() / "print_worker_config.json"
    return Path(__file__).with_name("print_worker_config.json")


def configure_logging() -> None:
    """Configura log persistente y consola sin depender del directorio actual."""
    log_dir = app_base_dir() / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_dir / "print_worker.log", encoding="utf-8"), logging.StreamHandler()],
    )


def post_json(url: str, payload: dict, worker_key: str | None = None) -> dict:
    """Envia JSON al backend con timeout para no bloquear el ciclo completo."""
    headers = {"Content-Type": "application/json"}
    if worker_key:
        headers["X-Kanpai-Worker-Key"] = worker_key
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=10) as response:  # noqa: S310 - URL local configurada por operador
        return json.loads(response.read().decode())


def get_json(url: str) -> dict:
    """Lee JSON del backend con timeout corto para autodeteccion local."""
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    with urlopen(request, timeout=2) as response:  # noqa: S310 - URL local configurada por operador
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def _kanpai_api_pids() -> set[int]:
    """Obtiene PIDs de kanpai-api.exe sin dependencias externas."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq kanpai-api.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
    except Exception:
        return set()

    pids: set[int] = set()
    for line in result.stdout.splitlines():
        clean = line.strip()
        if not clean or clean.startswith("INFO:"):
            continue
        parts = [item.strip().strip('"') for item in clean.split('","')]
        if len(parts) >= 2 and parts[0].lower() == "kanpai-api.exe":
            try:
                pids.add(int(parts[1]))
            except ValueError:
                continue
    return pids


def _listening_ports_for_pids(pids: set[int]) -> list[int]:
    """Obtiene puertos TCP locales en LISTENING para los PIDs indicados."""
    if not pids:
        return []

    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []

    ports: set[int] = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        proto, local_address, _foreign_address, state, pid_text = parts[:5]
        if proto.upper() != "TCP" or state.upper() != "LISTENING":
            continue
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if pid not in pids:
            continue
        if not local_address.startswith("127.0.0.1:"):
            continue
        try:
            ports.add(int(local_address.rsplit(":", 1)[1]))
        except ValueError:
            continue

    return sorted(ports)


def discover_local_api_base_url() -> str:
    """Detecta el backend local empaquetado cuando kanpai-api.exe usa puerto dinamico."""
    ports = _listening_ports_for_pids(_kanpai_api_pids())

    for port in ports:
        base = f"http://127.0.0.1:{port}"
        try:
            get_json(f"{base}/health")
            return base
        except Exception:
            continue

    raise RuntimeError("No se encontro kanpai-api.exe local respondiendo /health.")


def resolve_api_base_url(config: dict) -> str:
    """Resuelve URL fija o autodetectada del backend."""
    configured = str(config.get("api_base_url", "")).strip()

    if configured.lower() in {"auto", "dynamic", "local-kanpai-api"} or config.get("auto_discover_api_base_url") is True:
        return discover_local_api_base_url()

    if not configured:
        raise ValueError("Config del worker requiere api_base_url o api_base_url='auto'.")

    return configured.rstrip("/")


def encode_print_content(content: str) -> bytes:
    """Codifica texto para impresoras termicas POS-58."""
    return (content + "\n\n\n").encode("cp858", errors="replace")


def print_windows(printer_name: str, content: str) -> None:
    """Imprime texto RAW mediante pywin32 sobre una cola Windows."""
    try:
        import win32print
    except ImportError as error:
        raise RuntimeError("pywin32 no esta instalado; use --dry-run o instalelo en el entorno del worker.") from error

    handle = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(handle, 1, ("Kanpai POS", None, "RAW"))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, encode_print_content(content))
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)


def print_usb_device_path(device_path: str, content: str) -> None:
    """Imprime directo a una interfaz USBPRINT por device path, sin cola Windows."""
    if not hasattr(ctypes, "WinDLL"):
        raise RuntimeError("USB directo solo esta disponible en Windows.")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE

    kernel32.WriteFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    kernel32.WriteFile.restype = wintypes.BOOL

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    generic_write = 0x40000000
    file_share_read = 0x00000001
    file_share_write = 0x00000002
    open_existing = 3
    file_attribute_normal = 0x00000080
    invalid_handle_value = ctypes.c_void_p(-1).value

    handle = kernel32.CreateFileW(
        device_path,
        generic_write,
        file_share_read | file_share_write,
        None,
        open_existing,
        file_attribute_normal,
        None,
    )

    if handle == invalid_handle_value:
        raise ctypes.WinError(ctypes.get_last_error())

    payload = b"\x1b@" + encode_print_content(content) + b"\n"
    buffer = ctypes.create_string_buffer(payload)
    written = wintypes.DWORD(0)

    try:
        ok = kernel32.WriteFile(handle, buffer, len(payload), ctypes.byref(written), None)
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
        if written.value != len(payload):
            raise RuntimeError(f"Escritura USB incompleta: {written.value}/{len(payload)} bytes")
    finally:
        kernel32.CloseHandle(handle)


def resolve_printer_target(printer_target: PrinterTarget) -> tuple[str, str]:
    """Normaliza configuracion legacy string o configuracion extendida por modo."""
    if isinstance(printer_target, str):
        return "windows", printer_target

    if not isinstance(printer_target, dict):
        raise TypeError("La configuracion de impresora debe ser string o dict.")

    mode = str(printer_target.get("mode", "windows")).strip().lower()
    target = printer_target.get("target") or printer_target.get("windows_name") or printer_target.get("name")

    if not isinstance(target, str) or not target.strip():
        raise ValueError("La configuracion de impresora requiere target/windows_name/name.")

    return mode, target.strip()


def printer_target_label(printer_target: PrinterTarget) -> str:
    """Etiqueta legible para logs."""
    try:
        mode, target = resolve_printer_target(printer_target)
    except Exception:
        return repr(printer_target)
    if mode == "windows":
        return target
    return f"{mode}:{target}"


def print_configured_target(printer_target: PrinterTarget, content: str) -> None:
    """Despacha impresion al backend fisico configurado."""
    mode, target = resolve_printer_target(printer_target)

    if mode in {"windows", "win32print"}:
        print_windows(target, content)
        return

    if mode in {"usb_device_path", "usb_direct"}:
        print_usb_device_path(target, content)
        return

    raise ValueError(f"Modo de impresora no soportado: {mode}")


def process_once(
    config: dict,
    *,
    dry_run: bool = False,
    http_post: HttpPost = post_json,
    printer: Printer = print_configured_target,
) -> int:
    """Procesa como maximo un trabajo por clave y confirma siempre su resultado."""
    base = resolve_api_base_url(config)
    worker_id = config["worker_id"]
    worker_key = config.get("worker_key")
    processed = 0

    for printer_key, printer_target in config["printers"].items():
        claimed = http_post(
            f"{base}/api/v1/printing/jobs/claim-next",
            {"printer_key": printer_key, "worker_id": worker_id},
            worker_key,
        )
        job = claimed.get("job")
        if not job:
            continue

        processed += 1
        label = printer_target_label(printer_target)

        try:
            if dry_run:
                logging.info("DRY-RUN job=%s printer=%s content=%r", job["id"], label, job["content_snapshot"])
            else:
                printer(printer_target, job["content_snapshot"])
            http_post(f"{base}/api/v1/printing/jobs/{job['id']}/printed", {"worker_id": worker_id}, worker_key)
        except Exception as error:
            logging.exception("Fallo job=%s printer=%s", job["id"], label)
            http_post(
                f"{base}/api/v1/printing/jobs/{job['id']}/failed",
                {"worker_id": worker_id, "error_message": str(error)[:1000]},
                worker_key,
            )

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker fisico de impresion Kanpai POS para Windows")
    parser.add_argument("--config", default=str(default_config_path()))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    configure_logging()
    config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))

    while True:
        try:
            process_once(config, dry_run=args.dry_run)
        except Exception:
            logging.exception("Error de comunicacion en ciclo del worker")

        if args.once:
            return

        time.sleep(max(float(config.get("poll_seconds", 2)), 0.2))


if __name__ == "__main__":
    main()
