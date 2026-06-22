from __future__ import annotations

from datetime import datetime
from textwrap import wrap
from typing import Any, Mapping
from unicodedata import normalize

WIDTH_58MM = 32
WIDTH_STATION_58MM = WIDTH_58MM


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = normalize("NFKC", text)
    return text.strip()


def _money(cents: Any) -> str:
    try:
        amount = int(cents or 0) / 100
    except (TypeError, ValueError):
        amount = 0
    return f"${amount:,.0f}"


def _short_datetime(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%d/%m/%Y %H:%M")
        except ValueError:
            continue
    return text[:16]


def _hr(width: int, char: str = "-") -> str:
    return char * width


def _center(text: Any, width: int) -> str:
    return _clean(text).upper()[:width].center(width)


def _wrap_text(text: Any, width: int, prefix: str = "") -> list[str]:
    clean = _clean(text)
    if not clean:
        return []
    usable_width = max(width - len(prefix), 8)
    result: list[str] = []
    for raw_line in clean.split("\n"):
        wrapped = wrap(
            raw_line,
            width=usable_width,
            replace_whitespace=False,
            drop_whitespace=False,
        ) or [""]
        result.extend(f"{prefix}{line}"[:width] for line in wrapped)
    return result


def _kv(label: str, value: Any, width: int) -> list[str]:
    label_clean = _clean(label).upper()
    value_clean = _clean(value)
    if not value_clean:
        return []
    left = f"{label_clean}: "
    if len(left) + len(value_clean) <= width:
        return [f"{left}{value_clean}"[:width]]
    lines = [left[:width]]
    lines.extend(_wrap_text(value_clean, width, "  "))
    return lines


def _money_row(label: str, cents: Any, width: int) -> str:
    left = _clean(label).upper()
    right = _money(cents)
    space = max(width - len(left) - len(right), 1)
    return f"{left}{' ' * space}{right}"[:width]


def _append_variants(
    output: list[str],
    item: Mapping[str, Any],
    width: int,
    prefix: str = "  - ",
) -> None:
    variants = item.get("variants") or item.get("modifiers") or []
    for variant in variants:
        output.extend(_wrap_text(variant, width, prefix))


def _append_note(output: list[str], note: Any, width: int) -> None:
    clean_note = _clean(note)
    if clean_note:
        output.append("  NOTA:")
        output.extend(_wrap_text(clean_note, width, "    "))


def _ticket_item_lines(item: Mapping[str, Any], width: int) -> list[str]:
    quantity = _clean(item.get("quantity") or 1)
    name = _clean(item.get("name") or "Producto")
    total = _money(item.get("total_cents"))
    head = f"{quantity} x {name}"
    available = width - len(total) - 1

    output: list[str] = []
    if len(head) <= available:
        output.append(f"{head}{' ' * (width - len(head) - len(total))}{total}")
    else:
        wrapped = _wrap_text(head, width)
        output.extend(wrapped[:-1])
        last = wrapped[-1]
        if len(last) <= available:
            output.append(f"{last}{' ' * (width - len(last) - len(total))}{total}")
        else:
            output.append(last)
            output.append(total.rjust(width))

    _append_variants(output, item, width)
    _append_note(output, item.get("note"), width)
    return output


def _command_item_lines(item: Mapping[str, Any], width: int) -> list[str]:
    quantity = _clean(item.get("quantity") or 1)
    name = _clean(item.get("name") or "Producto").upper()
    output = _wrap_text(f"{quantity}  {name}", width)
    _append_variants(output, item, width)
    _append_note(output, item.get("note"), width)
    return output


def enforce_width(lines: list[str], width: int) -> list[str]:
    result: list[str] = []
    for line in lines:
        if len(line) <= width:
            result.append(line)
            continue
        result.extend(_wrap_text(line, width))
    return result


def render(lines: list[str], width: int) -> str:
    normalized = enforce_width(lines, width)
    return "\n".join(line[:width] for line in normalized).rstrip() + "\n"


def format_ticket_58mm(data: Mapping[str, Any]) -> str:
    width = WIDTH_58MM
    lines: list[str] = [
        _center(data.get("brand_name") or "SOMOS KANPAI", width),
        _center("TICKET", width),
        _hr(width),
    ]

    lines.extend(_kv("Folio", data.get("folio"), width))
    lines.extend(_kv("Mesa", data.get("table"), width))
    lines.extend(_kv("Fecha", _short_datetime(data.get("created_at")), width))
    lines.extend(_kv("Atendio", data.get("cashier"), width))
    lines.append(_hr(width))

    items = data.get("items") or []
    if items:
        for item in items:
            lines.extend(_ticket_item_lines(item, width))
    else:
        lines.append("SIN PRODUCTOS")

    lines.append(_hr(width))
    lines.append(_money_row("Subtotal", data.get("subtotal_cents"), width))
    discount_cents = int(data.get("discount_cents") or 0)
    if discount_cents:
        lines.append(_money_row("Descuento", discount_cents, width))
    lines.append(_money_row("Total", data.get("total_cents"), width))
    lines.append(_hr(width))

    payments = data.get("payments") or []
    if payments:
        for payment in payments:
            method = payment.get("method") or "Pago"
            lines.append(_money_row(method, payment.get("amount_cents"), width))

    ticket_message = data.get("ticket_message") or "ありがとうございました。またお待ちしております。"
    lines.append(_hr(width))
    lines.extend(_wrap_text(ticket_message, width))
    lines.extend(["", "", ""])
    return render(lines, width)


def format_command_58mm(data: Mapping[str, Any]) -> str:
    width = WIDTH_STATION_58MM
    title = data.get("title") or "COMANDA"
    lines: list[str] = [
        _center(f"*** {_clean(title)} ***", width),
        _hr(width, "="),
    ]
    lines.extend(_kv("Mesa", data.get("table"), width))
    lines.extend(_kv("Ticket", data.get("folio"), width))
    lines.extend(_kv("Ronda", data.get("round"), width))
    lines.extend(_kv("Hora", _short_datetime(data.get("created_at")), width))
    lines.extend(_kv("Estacion", _clean(data.get("station")).upper(), width))
    lines.append(_hr(width))

    items = data.get("items") or []
    if items:
        for index, item in enumerate(items):
            if index:
                lines.append("")
            lines.extend(_command_item_lines(item, width))
    else:
        lines.append("SIN PRODUCTOS")

    lines.extend(["", _hr(width, "="), "", ""])
    return render(lines, width)


def format_cancellation_58mm(data: Mapping[str, Any]) -> str:
    payload = dict(data)
    payload["title"] = "CANCELACION"
    output = format_command_58mm(payload).rstrip().splitlines()
    reason = data.get("reason")
    output.insert(-2, _hr(WIDTH_STATION_58MM))
    output.insert(-2, "CANCELAR PRODUCTO")
    if _clean(reason):
        output.insert(-2, "MOTIVO")
        output[-2:-2] = _wrap_text(reason, WIDTH_STATION_58MM)
    return render(output, WIDTH_STATION_58MM)


def format_modification_58mm(data: Mapping[str, Any]) -> str:
    width = WIDTH_STATION_58MM
    lines: list[str] = [
        _center("*** MODIFICACION ***", width),
        _hr(width, "="),
    ]
    lines.extend(_kv("Mesa", data.get("table"), width))
    lines.extend(_kv("Ticket", data.get("folio"), width))
    lines.extend(_kv("Hora", _short_datetime(data.get("created_at")), width))
    lines.extend(_kv("Estacion", _clean(data.get("station")).upper(), width))
    lines.append(_hr(width))
    lines.append("ANTES")
    for item in data.get("before_items") or []:
        lines.extend(_command_item_lines(item, width))
    lines.append(_hr(width))
    lines.append("DESPUES")
    for item in data.get("after_items") or []:
        lines.extend(_command_item_lines(item, width))
    reason = data.get("reason")
    if _clean(reason):
        lines.append(_hr(width))
        lines.append("MOTIVO")
        lines.extend(_wrap_text(reason, width))
    lines.extend(["", _hr(width, "="), "", ""])
    return render(lines, width)


def format_cash_shift_58mm(data: Mapping[str, Any]) -> str:
    width = WIDTH_58MM
    lines: list[str] = [
        _center(data.get("brand_name") or "SOMOS KANPAI", width),
        _center("CORTE", width),
        _hr(width),
    ]
    lines.extend(_kv("Folio", data.get("folio"), width))
    lines.extend(_kv("Abre", _short_datetime(data.get("opened_at")), width))
    lines.extend(_kv("Cierra", _short_datetime(data.get("closed_at")), width))
    lines.extend(_kv("Atendio", data.get("cashier"), width))
    lines.append(_hr(width))

    lines.append(_money_row("Ventas", data.get("net_sales_cents"), width))

    payments = [p for p in data.get("payments_by_method") or [] if int(p.get("amount_cents") or 0)]
    for payment in payments:
        lines.append(_money_row(payment.get("method") or "Pago", payment.get("amount_cents"), width))

    expense_cents = int(data.get("expense_cents") or 0)
    if expense_cents:
        lines.append(_money_row("Gastos", expense_cents, width))

    lines.append(_hr(width))
    lines.append(_money_row("Fondo inicial", data.get("opening_cash_cents"), width))
    lines.append(_money_row("Esperado", data.get("expected_cash_cents"), width))
    lines.append(_money_row("Contado", data.get("declared_cash_cents"), width))
    lines.append(_money_row("Diferencia", data.get("cash_difference_cents"), width))
    lines.append(_hr(width))
    lines.extend(_kv("Tickets", data.get("paid_ticket_count"), width))

    average = data.get("average_ticket_cents")
    if average:
        lines.append(_money_row("Promedio", average, width))

    note = data.get("note")
    if _clean(note):
        lines.append(_hr(width))
        lines.append("NOTA")
        lines.extend(_wrap_text(note, width))

    lines.extend(["", "", ""])
    return render(lines, width)


def sample_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")
