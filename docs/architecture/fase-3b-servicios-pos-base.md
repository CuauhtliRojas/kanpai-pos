# Kanpai POS - Fase 3-B: servicios POS base

## Objetivo

Esta fase introduce contratos Pydantic y servicios transaccionales para abrir el
corte de caja y un ticket en una mesa. La capa de servicio valida reglas, reserva
folios y hace `flush`; la capa HTTP es responsable de `commit` y `rollback`.

No se integran Airtable, impresión ni movimientos de inventario.

## Endpoints

- `POST /api/v1/pos/cash-shifts/open`: abre un corte de caja.
- `GET /api/v1/pos/cash-shifts/current`: obtiene el corte abierto.
- `POST /api/v1/pos/tables/{table_id}/open-ticket`: abre un ticket en una mesa.
- `GET /api/v1/pos/tickets/{ticket_id}`: obtiene un ticket por ID.

Los errores de negocio se exponen sin trazas internas: `400` para datos que no
cumplen el dominio, `404` para entidades inexistentes y `409` para conflictos de
estado.

## Servicios

- `folio_service.generate_folio`: reserva el siguiente número de una secuencia.
- `cash_shift_service.open_cash_shift`: valida y abre el corte.
- `cash_shift_service.get_current_cash_shift`: consulta el corte abierto.
- `table_service.get_free_active_table`: valida existencia, actividad y estado.
- `ticket_service.open_ticket_for_table`: crea el ticket y ocupa la mesa.
- `ticket_service.get_ticket`: consulta un ticket por ID.
- `exceptions`: define errores públicos del dominio por categoría.

## Reglas implementadas

- Las secuencias deben existir y estar activas; su contador se incrementa en la
  misma transacción que la operación.
- Solo puede existir un corte con estado `OPEN`.
- El empleado que abre una operación debe existir y estar activo.
- El efectivo inicial debe ser mayor o igual a cero.
- Para abrir un ticket debe existir un corte abierto.
- La mesa debe existir, estar activa y tener cache `FREE`.
- La mesa no puede tener otro ticket `OPEN` o `IN_PAYMENT`.
- El número de comensales debe ser mayor a cero.
- Si se especifica mesero, también debe existir y estar activo.
- Al abrir un ticket la mesa pasa a `OCCUPIED` y se registran eventos de estado y
  auditoría.

## Tablas afectadas

| Operación | Lecturas | Escrituras |
| --- | --- | --- |
| Generar folio | `folio_sequences` | `folio_sequences.next_number` |
| Abrir corte | `employees`, `cash_shifts`, `folio_sequences` | `cash_shifts`, `audit_events`, `folio_sequences` |
| Consultar corte | `cash_shifts` | Ninguna |
| Abrir ticket | `cash_shifts`, `employees`, `dining_tables`, `tickets`, `folio_sequences` | `tickets`, `dining_tables`, `table_status_events`, `audit_events`, `folio_sequences` |
| Consultar ticket | `tickets` | Ninguna |

## Pendiente para vender productos

Todavía faltan captura y modificación de líneas, precios y snapshots, cálculo de
totales y descuentos, comandas por estación, cobros y cierre del ticket/mesa.
También quedan fuera los movimientos de inventario y la cola de impresión.

## QA

```powershell
uv run python -m py_compile app\schemas\*.py app\services\*.py app\api\v1\routes\pos.py
uv run pytest
uv run ruff check .
```

Prueba manual con el servidor en el puerto local acordado:

```powershell
uv run uvicorn app.main:app --port 8010
curl.exe -X POST http://127.0.0.1:8010/api/v1/pos/cash-shifts/open -H "Content-Type: application/json" -d '{"employee_id":1,"opening_cash_cents":10000}'
curl.exe http://127.0.0.1:8010/api/v1/pos/cash-shifts/current
curl.exe -X POST http://127.0.0.1:8010/api/v1/pos/tables/1/open-ticket -H "Content-Type: application/json" -d '{"employee_id":1,"guest_count":2}'
curl.exe http://127.0.0.1:8010/api/v1/pos/tickets/1
```
