from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


DEFAULT_PRINT_PROFILE_PATH = Path("config/print_profile.json")


@dataclass(frozen=True)
class PrintProfile:
    brand_name: str = "SOMOS KANPAI"
    ticket_message: str = "Gracias por su visita."
    ascii_ticket_message: str = "Gracias por su visita."
    command_title: str = "COMANDA"
    cancel_title: str = "CANCELACION"
    modification_title: str = "MODIFICACION"
    cash_shift_title: str = "CORTE"
    show_decimals: bool = False

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Configuracion de impresion invalida: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"Configuracion de impresion debe ser objeto JSON: {path}")
    return payload


def get_print_profile(path: str | Path | None = None) -> PrintProfile:
    configured_path = path or os.getenv("KANPAI_PRINT_PROFILE_PATH")
    profile_path = Path(configured_path) if configured_path else DEFAULT_PRINT_PROFILE_PATH
    payload = _read_json(profile_path)

    defaults = PrintProfile().model_dump()
    merged = {
        key: payload.get(key, default)
        for key, default in defaults.items()
    }

    for key in (
        "brand_name",
        "ticket_message",
        "ascii_ticket_message",
        "command_title",
        "cancel_title",
        "modification_title",
        "cash_shift_title",
    ):
        value = merged[key]
        if not isinstance(value, str) or not value.strip():
            merged[key] = defaults[key]
        else:
            merged[key] = value.strip()

    merged["show_decimals"] = bool(merged["show_decimals"])
    return PrintProfile(**merged)
