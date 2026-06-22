from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from app.services.print_profile import get_print_profile
from app.services.print_formatters import (
    format_cash_shift_58mm,
    format_command_58mm,
    format_ticket_58mm,
)

DB_PATH = Path("data/kanpai_pos.db")
DEFAULT_OUTPUT_DIR = Path("_tmp_print_previews_real")


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit(f"No existe la base SQLite: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    if not table_exists(conn, table):
        return []
    return [dict(row)["name"] for row in conn.execute(f"PRAGMA table_info({table})")]


def first_col(columns: list[str], candidates: list[str]) -> str | None:
    lower_map = {col.lower(): col for col in columns}
    for candidate in candidates:
        found = lower_map.get(candidate.lower())
        if found:
            return found
    return None


def fetch_one(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> dict[str, Any] | None:
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def fetch_all(
    conn: sqlite3.Connection,
    sql: str,
    params: tuple[Any, ...] = (),
) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def row_value(row: dict[str, Any] | None, candidates: list[str], default: Any = None) -> Any:
    if not row:
        return default
    lower_map = {key.lower(): key for key in row}
    for candidate in candidates:
        key = lower_map.get(candidate.lower())
        if key is not None and row.get(key) is not None:
            return row[key]
    return default


def to_cents(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("$", "").replace(",", "")
    try:
        if "." in text:
            return int(round(float(text) * 100))
        return int(text)
    except ValueError:
        return 0


def money_text_to_cents(text: str) -> int:
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d{1,2})?", text)
    return to_cents(match.group(0)) if match else 0


def write_text(output_dir: Path, filename: str, content: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(path)


def write_json(output_dir: Path, filename: str, payload: Any) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(path)


def latest_print_job(conn: sqlite3.Connection, job_type: str) -> dict[str, Any] | None:
    if not table_exists(conn, "trabajos_impresion"):
        return None
    return fetch_one(
        conn,
        """
        SELECT *
        FROM trabajos_impresion
        WHERE trabajo_tipo = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (job_type,),
    )


def by_id(conn: sqlite3.Connection, table: str, row_id: Any) -> dict[str, Any] | None:
    if row_id is None or not table_exists(conn, table):
        return None
    return fetch_one(conn, f"SELECT * FROM {table} WHERE id = ?", (row_id,))


def display_name(row: dict[str, Any] | None, fallback: str = "") -> str:
    if not row:
        return fallback
    direct = row_value(
        row,
        [
            "visualizacion_nombre",
            "alias_pos",
            "completo_nombre",
            "display_name",
            "nombre_visible",
            "mesa_codigo",
            "empleado_codigo",
            "name",
            "nombre",
            "full_name",
            "nombre_completo",
            "method_name",
            "metodo_nombre",
            "method_key",
            "metodo_clave",
        ],
    )
    if direct:
        return str(direct)

    first = row_value(row, ["first_name", "nombre_pila"], "")
    last = row_value(row, ["last_name", "apellido"], "")
    full = f"{first} {last}".strip()
    return full or fallback


def business_config(conn: sqlite3.Connection) -> dict[str, Any]:
    profile = get_print_profile()

    business_name = profile.brand_name
    logo_path = ""

    for table in ["configuracion_negocio", "configuracion_pos"]:
        if table_exists(conn, table):
            row = fetch_one(conn, f"SELECT * FROM {table} ORDER BY id LIMIT 1") or {}
            business_name = row_value(
                row,
                ["business_name", "negocio_nombre", "name", "nombre"],
                profile.brand_name,
            )
            logo_path = row_value(row, ["logo_path", "logotipo_ruta"], "")
            break

    return {
        "business_name": business_name,
        "brand_name": profile.brand_name,
        "ticket_message": profile.ticket_message,
        "ascii_ticket_message": profile.ascii_ticket_message,
        "logo_path": logo_path,
    }

def latest_ticket_for_print_job(
    conn: sqlite3.Connection,
    print_job: dict[str, Any] | None,
) -> dict[str, Any] | None:
    ticket_id = row_value(print_job, ["ticket_id"])
    ticket = by_id(conn, "tickets", ticket_id)
    if ticket:
        return ticket

    if not table_exists(conn, "tickets"):
        return None

    return fetch_one(conn, "SELECT * FROM tickets ORDER BY id DESC LIMIT 1")


def build_ticket_items(
    conn: sqlite3.Connection,
    ticket: dict[str, Any],
    diagnostics: dict[str, Any],
) -> list[dict[str, Any]]:
    if not table_exists(conn, "lineas_ticket"):
        diagnostics["ticket_items_error"] = "No existe lineas_ticket."
        return []

    cols = table_columns(conn, "lineas_ticket")
    ticket_col = first_col(cols, ["ticket_id", "ticketId"])
    if not ticket_col:
        diagnostics["ticket_items_error"] = {
            "reason": "No se encontro FK ticket en lineas_ticket.",
            "columns": cols,
        }
        return []

    line_rows = fetch_all(
        conn,
        f"SELECT * FROM lineas_ticket WHERE {ticket_col} = ? ORDER BY id",
        (ticket["id"],),
    )

    quantity_col = first_col(cols, ["quantity", "cantidad"])
    name_col = first_col(
        cols,
        [
            "product_name_snapshot",
            "producto_nombre_instantanea",
            "nombre_producto_instantanea",
            "product_name",
            "producto_nombre",
            "name",
            "nombre",
        ],
    )
    total_col = first_col(
        cols,
        [
            "linea_total_centavos",
            "total_cents",
            "line_total_cents",
            "total_linea_centavos",
            "total_centavos",
            "importe_centavos",
            "subtotal_cents",
            "subtotal_centavos",
        ],
    )
    unit_col = first_col(cols, ["unidad_precio_centavos", "unit_price_cents", "precio_unitario_centavos"])
    note_col = first_col(cols, ["note", "nota", "notes", "notas"])
    variant_cols = [
        col
        for col in cols
        if any(
            token in col.lower()
            for token in ["variant", "variante", "modifier", "modificador", "preparacion"]
        )
    ]

    items: list[dict[str, Any]] = []
    for line in line_rows:
        quantity = row_value(line, [quantity_col] if quantity_col else [], 1)
        total = row_value(line, [total_col] if total_col else [], None)
        if total is None and unit_col:
            total = to_cents(row_value(line, [unit_col], 0)) * int(quantity or 1)

        variants = []
        for col in variant_cols:
            raw = line.get(col)
            if raw:
                variants.append(str(raw))

        items.append(
            {
                "quantity": quantity,
                "name": row_value(line, [name_col] if name_col else [], f"Linea {line['id']}"),
                "total_cents": to_cents(total),
                "note": row_value(line, [note_col] if note_col else [], ""),
                "variants": variants,
            }
        )

    diagnostics["ticket_items_columns_used"] = {
        "ticket_col": ticket_col,
        "quantity_col": quantity_col,
        "name_col": name_col,
        "total_col": total_col,
        "unit_col": unit_col,
        "note_col": note_col,
        "variant_cols": variant_cols,
        "rows": len(items),
    }
    return items


def build_ticket_payments(
    conn: sqlite3.Connection,
    ticket: dict[str, Any],
    diagnostics: dict[str, Any],
) -> list[dict[str, Any]]:
    if not table_exists(conn, "pagos"):
        diagnostics["ticket_payments_error"] = "No existe pagos."
        return []

    cols = table_columns(conn, "pagos")
    ticket_col = first_col(cols, ["ticket_id", "ticketId"])
    if not ticket_col:
        diagnostics["ticket_payments_error"] = {
            "reason": "No se encontro FK ticket en pagos.",
            "columns": cols,
        }
        return []

    payment_rows = fetch_all(
        conn,
        f"SELECT * FROM pagos WHERE {ticket_col} = ? ORDER BY id",
        (ticket["id"],),
    )

    amount_col = first_col(cols, ["amount_cents", "monto_centavos", "importe_centavos"])
    method_id_col = first_col(cols, ["pago_metodo_id", "payment_method_id", "metodo_pago_id", "method_id"])
    method_text_col = first_col(
        cols,
        ["payment_method_key", "metodo_pago_clave", "method_key", "metodo"],
    )

    payments: list[dict[str, Any]] = []
    for payment in payment_rows:
        method = row_value(payment, [method_text_col] if method_text_col else [], "")
        if not method and method_id_col and table_exists(conn, "metodos_pago"):
            method_row = by_id(conn, "metodos_pago", payment.get(method_id_col))
            method = display_name(method_row, "Pago")

        payments.append(
            {
                "method": method or "Pago",
                "amount_cents": to_cents(row_value(payment, [amount_col] if amount_col else [], 0)),
            }
        )

    diagnostics["ticket_payments_columns_used"] = {
        "ticket_col": ticket_col,
        "amount_col": amount_col,
        "method_id_col": method_id_col,
        "method_text_col": method_text_col,
        "rows": len(payments),
    }
    return payments


def parse_ticket_snapshot(snapshot: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "business_name": "KANPAI",
        "folio": "",
        "table": "",
        "created_at": "",
        "cashier": "",
        "waiter": "",
        "items": [],
        "subtotal_cents": 0,
        "discount_cents": 0,
        "total_cents": 0,
        "payments": [],
        "ticket_message": "",
    }

    in_payments = False
    for raw in snapshot.splitlines():
        line = raw.strip()
        lower = line.lower()

        if lower.startswith("folio:"):
            data["folio"] = line.split(":", 1)[1].strip()
        elif lower.startswith("mesa:"):
            data["table"] = line.split(":", 1)[1].strip()
        elif lower.startswith("total:"):
            data["total_cents"] = money_text_to_cents(line)
        elif lower == "pagos:":
            in_payments = True
        elif in_payments and ":" in line:
            method, amount = line.split(":", 1)
            data["payments"].append(
                {"method": method.strip(), "amount_cents": money_text_to_cents(amount)}
            )
        elif line and not data["business_name"]:
            data["business_name"] = line

    data["subtotal_cents"] = data["total_cents"]
    data["ticket_message"] = "GRACIAS"
    return data


def build_ticket_data(conn: sqlite3.Connection, diagnostics: dict[str, Any]) -> dict[str, Any] | None:
    cfg = business_config(conn)
    job = latest_print_job(conn, "Ticket")
    ticket = latest_ticket_for_print_job(conn, job)

    if not ticket:
        diagnostics["ticket_error"] = "No hay ticket estructurado; se usara snapshot si existe."
        if job and job.get("instantanea_contenido"):
            data = parse_ticket_snapshot(str(job["instantanea_contenido"]))
            data["business_name"] = cfg["business_name"]
            data["created_at"] = job.get("creacion_fecha") or ""
            data["ticket_message"] = cfg["ticket_message"] or data["ticket_message"]
            return data
        return None

    cols = list(ticket.keys())
    table_id = row_value(ticket, ["table_id", "mesa_id"])
    cashier_id = row_value(
        ticket,
        [
            "closed_by_employee_id",
            "cierre_por_empleado_id",
            "opened_by_employee_id",
            "apertura_por_empleado_id",
            "employee_id",
            "empleado_id",
        ],
    )
    waiter_id = row_value(ticket, ["waiter_employee_id", "mesero_empleado_id"])

    table = by_id(conn, "mesas", table_id)
    cashier = by_id(conn, "empleados", cashier_id)
    waiter = by_id(conn, "empleados", waiter_id)

    data = {
        "business_name": cfg["business_name"],
        "brand_name": cfg.get("brand_name", "SOMOS KANPAI"),
        "folio": row_value(ticket, ["folio"], ""),
        "table": display_name(table, f"Mesa {table_id or ''}".strip()),
        "created_at": row_value(
            ticket,
            ["closed_at", "cierre_fecha", "opened_at", "apertura_fecha", "created_at", "creacion_fecha"],
            row_value(job, ["creacion_fecha"], ""),
        ),
        "cashier": display_name(cashier, f"Empleado {cashier_id or ''}".strip()),
        "waiter": display_name(waiter, ""),
        "items": build_ticket_items(conn, ticket, diagnostics),
        "subtotal_cents": to_cents(
            row_value(ticket, ["subtotal_cents", "subtotal_centavos"], 0)
        ),
        "discount_cents": to_cents(
            row_value(ticket, ["discount_cents", "descuento_centavos"], 0)
        ),
        "total_cents": to_cents(row_value(ticket, ["total_cents", "total_centavos"], 0)),
        "payments": build_ticket_payments(conn, ticket, diagnostics),
        "ticket_message": cfg["ticket_message"] or "GRACIAS",
    }

    diagnostics["ticket_source"] = {
        "print_job_id": row_value(job, ["id"]),
        "ticket_id": ticket.get("id"),
        "ticket_columns": cols,
    }

    return data


def parse_command_snapshot(
    snapshot: str,
    job: dict[str, Any] | None = None,
    table_name: str = "",
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "folio": "",
        "table": table_name,
        "created_at": row_value(job, ["creacion_fecha"], "") if job else "",
        "station": "",
        "round": "",
        "items": [],
    }

    current_item: dict[str, Any] | None = None
    for raw in snapshot.splitlines():
        line = raw.strip()
        lower = line.lower()

        if lower.startswith("ticket:"):
            data["folio"] = line.split(":", 1)[1].strip()
        elif lower.startswith("estacion:"):
            data["station"] = line.split(":", 1)[1].strip()
        elif lower.startswith("ronda:"):
            data["round"] = line.split(":", 1)[1].strip()
        elif " x " in line and not line.startswith("-"):
            quantity, name = line.split(" x ", 1)
            current_item = {
                "quantity": quantity.strip(),
                "name": name.strip(),
                "variants": [],
            }
            data["items"].append(current_item)
        elif line.startswith("-") and current_item:
            current_item["variants"].append(line[1:].strip())

    return data


def build_command_data(conn: sqlite3.Connection, diagnostics: dict[str, Any]) -> dict[str, Any] | None:
    job = latest_print_job(conn, "Comanda")
    if not job:
        diagnostics["comanda_error"] = "No hay trabajo Comanda."
        return None

    table_name = ""
    ticket = by_id(conn, "tickets", job.get("ticket_id"))
    if ticket:
        table_id = row_value(ticket, ["table_id", "mesa_id"])
        table = by_id(conn, "mesas", table_id)
        table_name = display_name(table, f"Mesa {table_id or ''}".strip())

    diagnostics["comanda_source"] = {
        "print_job_id": job.get("id"),
        "ticket_id": job.get("ticket_id"),
        "command_batch_id": job.get("comanda_lote_id"),
        "station_order_id": job.get("estacion_orden_id"),
        "printer": job.get("clave_impresora_instantanea"),
    }

    return parse_command_snapshot(str(job.get("instantanea_contenido") or ""), job, table_name)


def parse_cash_shift_snapshot(snapshot: str, job: dict[str, Any] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "business_name": "KANPAI",
        "folio": "",
        "opened_at": "",
        "closed_at": row_value(job, ["creacion_fecha"], "") if job else "",
        "cashier": "",
        "gross_sales_cents": 0,
        "discount_cents": 0,
        "net_sales_cents": 0,
        "expense_cents": 0,
        "payments_by_method": [],
        "expected_cash_cents": 0,
        "declared_cash_cents": 0,
        "cash_difference_cents": 0,
        "paid_ticket_count": 0,
        "cancelled_ticket_count": 0,
        "note": "",
    }

    for raw in snapshot.splitlines():
        line = raw.strip()
        lower = line.lower()

        if lower.startswith("folio:"):
            data["folio"] = line.split(":", 1)[1].strip()
        elif lower.startswith("ventas:"):
            data["gross_sales_cents"] = money_text_to_cents(line)
            data["net_sales_cents"] = money_text_to_cents(line)
        elif lower.startswith("efectivo esperado:"):
            data["expected_cash_cents"] = money_text_to_cents(line)
        elif lower.startswith("efectivo declarado:"):
            data["declared_cash_cents"] = money_text_to_cents(line)
        elif lower.startswith("diferencia:"):
            data["cash_difference_cents"] = money_text_to_cents(line)
        elif lower.startswith("gastos:"):
            data["expense_cents"] = money_text_to_cents(line)
        elif lower.startswith("tickets pagados:"):
            data["paid_ticket_count"] = int(money_text_to_cents(line) / 100)
        elif lower.startswith("tickets cancelados:"):
            data["cancelled_ticket_count"] = int(money_text_to_cents(line) / 100)

    return data


def build_cash_shift_data(conn: sqlite3.Connection, diagnostics: dict[str, Any]) -> dict[str, Any] | None:
    cfg = business_config(conn)
    job = latest_print_job(conn, "Corte")
    cash_shift_id = row_value(job, ["caja_corte_id", "cash_shift_id"])
    cash_shift = by_id(conn, "cortes_caja", cash_shift_id)

    if not cash_shift and table_exists(conn, "cortes_caja"):
        cash_shift = fetch_one(conn, "SELECT * FROM cortes_caja ORDER BY id DESC LIMIT 1")

    if not cash_shift:
        diagnostics["corte_error"] = "No hay corte estructurado; se usara snapshot si existe."
        if job and job.get("instantanea_contenido"):
            data = parse_cash_shift_snapshot(str(job["instantanea_contenido"]), job)
            data["business_name"] = cfg["business_name"]
            return data
        return None

    cashier_id = row_value(
        cash_shift,
        [
            "closed_by_employee_id",
            "cierre_por_empleado_id",
            "opened_by_employee_id",
            "apertura_por_empleado_id",
            "employee_id",
            "empleado_id",
        ],
    )
    cashier = by_id(conn, "empleados", cashier_id)

    data = {
        "business_name": cfg["business_name"],
        "brand_name": cfg.get("brand_name", "SOMOS KANPAI"),
        "folio": row_value(cash_shift, ["folio"], ""),
        "opened_at": row_value(cash_shift, ["opened_at", "apertura_fecha"], ""),
        "closed_at": row_value(
            cash_shift,
            ["closed_at", "cierre_fecha"],
            row_value(job, ["creacion_fecha"], ""),
        ),
        "cashier": display_name(cashier, f"Empleado {cashier_id or ''}".strip()),
        "gross_sales_cents": to_cents(
            row_value(cash_shift, ["total_sales_cents", "ventas_total_centavos"], 0)
        ),
        "discount_cents": to_cents(
            row_value(cash_shift, ["discount_cents", "descuento_centavos"], 0)
        ),
        "net_sales_cents": to_cents(
            row_value(cash_shift, ["net_total_cents", "neto_total_centavos", "total_sales_cents"], 0)
        ),
        "opening_cash_cents": to_cents(
            row_value(cash_shift, ["opening_cash_cents", "apertura_caja_centavos"], 0)
        ),
        "expense_cents": to_cents(
            row_value(cash_shift, ["total_expenses_cents", "gastos_total_centavos"], 0)
        ),
        "payments_by_method": [
            {
                "method": "Efectivo",
                "amount_cents": to_cents(
                    row_value(cash_shift, ["cash_total_cents", "caja_total_centavos"], 0)
                ),
            },
            {
                "method": "Tarjeta",
                "amount_cents": to_cents(
                    row_value(cash_shift, ["card_total_cents", "tarjeta_total_centavos"], 0)
                ),
            },
            {
                "method": "Transferencia",
                "amount_cents": to_cents(
                    row_value(
                        cash_shift,
                        ["transfer_total_cents", "transferencia_total_centavos"],
                        0,
                    )
                ),
            },
        ],
        "expected_cash_cents": to_cents(
            row_value(cash_shift, ["expected_cash_cents", "esperado_caja_centavos"], 0)
        ),
        "declared_cash_cents": to_cents(
            row_value(cash_shift, ["declared_cash_cents", "declarado_caja_centavos"], 0)
        ),
        "cash_difference_cents": to_cents(
            row_value(cash_shift, ["cash_difference_cents", "caja_diferencia_centavos"], 0)
        ),
        "paid_ticket_count": row_value(cash_shift, ["ticket_count", "ticket_conteo"], 0),
        "average_ticket_cents": to_cents(
            row_value(cash_shift, ["average_ticket_cents", "promedio_ticket_centavos"], 0)
        ),
        "cancelled_ticket_count": row_value(
            cash_shift,
            ["cancelled_ticket_count", "tickets_cancelados_conteo"],
            0,
        ),
        "note": row_value(cash_shift, ["notes", "notas", "closing_note", "cierre_nota"], ""),
    }

    # Si el corte estructurado no tiene totales llenos, usar el snapshot real actual.
    if job and not data["gross_sales_cents"] and job.get("instantanea_contenido"):
        fallback = parse_cash_shift_snapshot(str(job["instantanea_contenido"]), job)
        fallback["business_name"] = data["business_name"]
        fallback["folio"] = data["folio"] or fallback["folio"]
        fallback["opened_at"] = data["opened_at"]
        fallback["closed_at"] = data["closed_at"]
        fallback["cashier"] = data["cashier"]
        data = fallback

    diagnostics["corte_source"] = {
        "print_job_id": row_value(job, ["id"]),
        "cash_shift_id": cash_shift.get("id"),
        "cash_shift_columns": list(cash_shift.keys()),
    }

    return data


def write_raw_snapshot(
    conn: sqlite3.Connection,
    output_dir: Path,
    job_type: str,
    filename: str,
) -> None:
    job = latest_print_job(conn, job_type)
    if not job:
        return

    content = "\n".join(
        [
            f"PRINT_JOB_ID: {job.get('id')}",
            f"TIPO: {job.get('trabajo_tipo')}",
            f"PRINTER: {job.get('clave_impresora_instantanea')}",
            f"ESTADO: {job.get('estado')}",
            f"CREADO: {job.get('creacion_fecha')}",
            "-" * 48,
            str(job.get("instantanea_contenido") or ""),
        ]
    )
    write_text(output_dir, filename, content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera previews con datos reales de SQLite.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    conn = connect()

    diagnostics: dict[str, Any] = {
        "db_path": str(DB_PATH),
        "tables": {},
        "errors": {},
    }

    for table in [
        "configuracion_negocio",
        "configuracion_pos",
        "trabajos_impresion",
        "tickets",
        "lineas_ticket",
        "pagos",
        "metodos_pago",
        "descuentos_ticket",
        "mesas",
        "empleados",
        "cortes_caja",
    ]:
        diagnostics["tables"][table] = {
            "exists": table_exists(conn, table),
            "columns": table_columns(conn, table),
        }

    for job_type, filename in [
        ("Ticket", "raw_snapshot_ticket_real.txt"),
        ("Comanda", "raw_snapshot_comanda_real.txt"),
        ("Corte", "raw_snapshot_corte_real.txt"),
        ("Cancelacion comanda", "raw_snapshot_cancelacion_real.txt"),
        ("Modificacion", "raw_snapshot_modificacion_real.txt"),
    ]:
        write_raw_snapshot(conn, output_dir, job_type, filename)

    try:
        ticket_data = build_ticket_data(conn, diagnostics)
        if ticket_data:
            write_json(output_dir, "ticket_real_data.json", ticket_data)
            write_text(output_dir, "ticket_58mm_real.txt", format_ticket_58mm(ticket_data))
    except Exception as exc:
        diagnostics["errors"]["ticket"] = f"{type(exc).__name__}: {exc}"

    try:
        command_data = build_command_data(conn, diagnostics)
        if command_data:
            write_json(output_dir, "comanda_real_data.json", command_data)
            write_text(output_dir, "comanda_58mm_real.txt", format_command_58mm(command_data))
    except Exception as exc:
        diagnostics["errors"]["comanda"] = f"{type(exc).__name__}: {exc}"

    try:
        cash_shift_data = build_cash_shift_data(conn, diagnostics)
        if cash_shift_data:
            write_json(output_dir, "corte_real_data.json", cash_shift_data)
            write_text(output_dir, "corte_58mm_real.txt", format_cash_shift_58mm(cash_shift_data))
    except Exception as exc:
        diagnostics["errors"]["corte"] = f"{type(exc).__name__}: {exc}"

    write_json(output_dir, "diagnostico_datos_reales.json", diagnostics)


if __name__ == "__main__":
    main()
