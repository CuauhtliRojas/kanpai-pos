from __future__ import annotations

from app.services.print_formatters import (
    WIDTH_58MM,
    WIDTH_80MM,
    format_cancellation_80mm,
    format_cash_shift_58mm,
    format_command_80mm,
    format_modification_80mm,
    format_ticket_58mm,
)


def assert_width(content: str, width: int) -> None:
    for line in content.splitlines():
        assert len(line) <= width, f"{len(line)} > {width}: {line!r}"


def test_ticket_58mm_preview_width_and_content() -> None:
    content = format_ticket_58mm(
        {
            "brand_name": "SOMOS KANPAI",
            "folio": "TK-1",
            "table": "Mesa 1",
            "created_at": "2026-06-22 13:30",
            "cashier": "Admin",
            "items": [
                {
                    "quantity": 2,
                    "name": "Producto largo para prueba de wrap",
                    "total_cents": 12300,
                    "variants": ["Variante larga para envolver"],
                    "note": "Nota libre de prueba.",
                }
            ],
            "subtotal_cents": 12300,
            "discount_cents": 1000,
            "total_cents": 11300,
            "payments": [{"method": "Efectivo", "amount_cents": 11300}],
            "ticket_message": "ありがとうございました。またお待ちしております。",
        }
    )

    assert "SOMOS KANPAI" in content
    assert "TICKET" in content
    assert "TK-1" in content
    assert "$113" in content
    assert ".00" not in content
    assert_width(content, WIDTH_58MM)


def test_command_80mm_preview_width_and_content() -> None:
    content = format_command_80mm(
        {
            "folio": "CMD-1",
            "table": "Mesa 2",
            "created_at": "2026-06-22 13:30",
            "station": "Cocina",
            "round": 1,
            "items": [
                {
                    "quantity": 3,
                    "name": "Yakitori",
                    "variants": ["Tare"],
                    "note": "Una sin sal otra con doble mezcal",
                }
            ],
        }
    )

    assert "COMANDA" in content
    assert "COCINA" in content
    assert "NOTA" in content
    assert "doble mezcal" in content
    assert_width(content, WIDTH_80MM)


def test_cancellation_80mm_preview_width_and_content() -> None:
    content = format_cancellation_80mm(
        {
            "folio": "CAN-1",
            "table": "Mesa 2",
            "created_at": "2026-06-22 13:30",
            "station": "Cocina",
            "round": 1,
            "items": [{"quantity": 1, "name": "Yakitori"}],
            "reason": "Cliente cancela.",
        }
    )

    assert "CANCELACION" in content
    assert "CANCELAR PRODUCTO" in content
    assert_width(content, WIDTH_80MM)


def test_modification_80mm_preview_width_and_content() -> None:
    content = format_modification_80mm(
        {
            "folio": "MOD-1",
            "table": "Mesa 2",
            "created_at": "2026-06-22 13:30",
            "station": "Cocina",
            "before_items": [{"quantity": 1, "name": "Ramen"}],
            "after_items": [{"quantity": 1, "name": "Ramen", "variants": ["Sin picante"]}],
            "reason": "Cambio solicitado.",
        }
    )

    assert "MODIFICACION" in content
    assert "ANTES" in content
    assert "DESPUES" in content
    assert_width(content, WIDTH_80MM)


def test_cash_shift_58mm_preview_width_and_content() -> None:
    content = format_cash_shift_58mm(
        {
            "brand_name": "SOMOS KANPAI",
            "folio": "CT-1",
            "opened_at": "2026-06-22 12:00",
            "closed_at": "2026-06-22 18:00",
            "cashier": "Admin",
            "net_sales_cents": 49000,
            "payments_by_method": [{"method": "Efectivo", "amount_cents": 49000}],
            "opening_cash_cents": 100000,
            "expected_cash_cents": 149000,
            "declared_cash_cents": 149000,
            "cash_difference_cents": 0,
            "paid_ticket_count": 4,
            "average_ticket_cents": 12250,
        }
    )

    assert "CORTE" in content
    assert "CT-1" in content
    assert "$490" in content
    assert ".00" not in content
    assert_width(content, WIDTH_58MM)
