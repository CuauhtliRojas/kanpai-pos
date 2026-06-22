from __future__ import annotations

import argparse
from pathlib import Path

from app.services.print_formatters import (
    format_cancellation_80mm,
    format_cash_shift_58mm,
    format_command_80mm,
    format_modification_80mm,
    format_ticket_58mm,
    sample_now,
)
from app.services.print_profile import get_print_profile


def write_preview(output_dir: Path, filename: str, content: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    print(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera previews offline de impresion.")
    parser.add_argument(
        "--output-dir",
        default="_tmp_print_previews",
        help="Carpeta de salida para previews txt.",
    )
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    profile = get_print_profile()

    ticket_data = {
        "business_name": "Kanpai",
        "brand_name": profile.brand_name,
        "folio": "TK-000123",
        "table": "Mesa 4",
        "created_at": sample_now(),
        "cashier": "Admin",
        "waiter": "Admin",
        "items": [
            {
                "quantity": 2,
                "name": "Yakitori de pollo",
                "total_cents": 18000,
                "variants": ["Salsa tare", "Termino dorado"],
                "note": "Sin cebollin",
            },
            {
                "quantity": 1,
                "name": "Ramen tonkotsu especial",
                "total_cents": 16500,
                "variants": ["Picante medio", "Extra huevo"],
            },
            {
                "quantity": 3,
                "name": "Agua mineral",
                "total_cents": 10500,
            },
        ],
        "subtotal_cents": 45000,
        "discount_cents": 5000,
        "total_cents": 40000,
        "payments": [
            {"method": "Efectivo", "amount_cents": 25000},
            {"method": "Tarjeta", "amount_cents": 15000},
        ],
        "ticket_message": profile.ticket_message,
        "ascii_ticket_message": profile.ascii_ticket_message,
    }

    command_data = {
        "folio": "CMD-000456",
        "table": "Mesa 4",
        "created_at": sample_now(),
        "station": "Cocina",
        "round": 2,
        "items": [
            {
                "quantity": 2,
                "name": "Yakitori de pollo",
                "variants": ["Salsa tare", "Termino dorado"],
                "note": "Uno sin cebollin",
            },
            {
                "quantity": 1,
                "name": "Ramen tonkotsu especial",
                "variants": ["Picante medio", "Extra huevo"],
            },
        ],
    }

    cancellation_data = {
        **command_data,
        "folio": "CAN-000789",
        "items": [
            {
                "quantity": 1,
                "name": "Yakitori de pollo",
                "variants": ["Salsa tare"],
            }
        ],
        "reason": "Cliente cancela un platillo antes de preparacion.",
    }

    modification_data = {
        "folio": "MOD-000321",
        "table": "Mesa 4",
        "created_at": sample_now(),
        "station": "Cocina",
        "before_items": [
            {
                "quantity": 1,
                "name": "Ramen tonkotsu especial",
                "variants": ["Picante medio"],
            }
        ],
        "after_items": [
            {
                "quantity": 1,
                "name": "Ramen tonkotsu especial",
                "variants": ["Sin picante", "Extra huevo"],
                "note": "Cambio solicitado por cliente",
            }
        ],
        "reason": "Correccion antes de preparar.",
    }

    cash_shift_data = {
        "business_name": "Kanpai",
        "brand_name": profile.brand_name,
        "folio": "CT-000010",
        "opened_at": "2026-06-22 12:00",
        "closed_at": sample_now(),
        "cashier": "Admin",
        "net_sales_cents": 115000,
        "payments_by_method": [
            {"method": "Efectivo", "amount_cents": 60000},
            {"method": "Tarjeta", "amount_cents": 55000},
        ],
        "opening_cash_cents": 100000,
        "expected_cash_cents": 160000,
        "declared_cash_cents": 159500,
        "cash_difference_cents": -500,
        "paid_ticket_count": 9,
        "average_ticket_cents": 12777,
        "note": "Cierre de prueba para validar formato.",
    }

    write_preview(output_dir, "ticket_58mm.txt", format_ticket_58mm(ticket_data))
    write_preview(output_dir, "comanda_80mm.txt", format_command_80mm(command_data))
    write_preview(
        output_dir,
        "cancelacion_comanda_80mm.txt",
        format_cancellation_80mm(cancellation_data),
    )
    write_preview(
        output_dir,
        "modificacion_80mm.txt",
        format_modification_80mm(modification_data),
    )
    write_preview(output_dir, "corte_58mm.txt", format_cash_shift_58mm(cash_shift_data))


if __name__ == "__main__":
    main()
