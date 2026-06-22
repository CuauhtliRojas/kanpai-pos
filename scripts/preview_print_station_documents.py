from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.services.print_formatters import (
    format_cancellation_80mm,
    format_command_80mm,
    format_modification_80mm,
)

OUTPUT_DIR = Path("_tmp_print_previews_real")
COMANDA_DATA_PATH = OUTPUT_DIR / "comanda_real_data.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(
            f"No existe {path}. Primero ejecuta: uv run python -m scripts.preview_print_formats_from_db"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def write_preview(filename: str, content: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(path)


def first_item_or_sample(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("items") or []
    if items:
        item = deepcopy(items[0])
    else:
        item = {
            "quantity": 1,
            "name": "Producto de prueba",
            "variants": [],
        }

    item.setdefault("variants", [])
    return item


def main() -> None:
    base = read_json(COMANDA_DATA_PATH)

    # Misma comanda, mismo cuerpo, cambiando estacion.
    barra = deepcopy(base)
    barra["station"] = base.get("station") or "BARRA"
    write_preview("comanda_80mm_estacion_barra.txt", format_command_80mm(barra))

    cocina = deepcopy(base)
    cocina["station"] = "COCINA"
    cocina["items"] = [
        {
            "quantity": 2,
            "name": "Yakitori de pollo tempura/asada",
            "variants": ["Tempura", "Asada"],
            "note": "Una sin sal y otra con salsa aparte",
        },
        {
            "quantity": 1,
            "name": "Orden Yakitori combinada",
            "variants": ["Pollo", "Pulpo"],
            "note": "Sin cebolla",
        },
    ]
    write_preview("comanda_80mm_estacion_cocina_con_notas.txt", format_command_80mm(cocina))

    cocteleria = deepcopy(base)
    cocteleria["station"] = "BARRA"
    cocteleria["items"] = [
        {
            "quantity": 2,
            "name": "Moctel de Mango",
            "variants": ["Vaso alto"],
            "note": "Una sin sal, otra con doble mezcal",
        }
    ]
    write_preview(
        "comanda_80mm_estacion_barra_con_notas.txt",
        format_command_80mm(cocteleria),
    )

    cancelacion = deepcopy(base)
    cancelacion["items"] = [first_item_or_sample(base)]
    cancelacion["reason"] = "Cliente cancela antes de preparar."
    write_preview(
        "cancelacion_comanda_80mm_muestra.txt",
        format_cancellation_80mm(cancelacion),
    )

    modificacion = {
        "folio": base.get("folio"),
        "table": base.get("table"),
        "created_at": base.get("created_at"),
        "station": base.get("station") or "BARRA",
        "before_items": [
            {
                "quantity": 1,
                "name": "Moctel de Mango",
                "variants": ["Normal"],
                "note": "Sin cambios",
            }
        ],
        "after_items": [
            {
                "quantity": 1,
                "name": "Moctel de Mango",
                "variants": ["Vaso alto"],
                "note": "Sin sal y con doble mezcal",
            }
        ],
        "reason": "Correccion solicitada por mesa.",
    }
    write_preview("modificacion_80mm_muestra.txt", format_modification_80mm(modificacion))


if __name__ == "__main__":
    main()
