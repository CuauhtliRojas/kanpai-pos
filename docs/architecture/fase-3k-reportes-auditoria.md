# Fase 3-K: reportes y auditoría operativa mínima

## Objetivo

Exponer consultas locales para validar ventas, caja, inventario, impresión y el
ciclo completo de tickets y cortes antes de diseñar la sincronización con
Airtable. Esta fase no persiste agregados ni agrega dependencias.

Todos los reportes aceptan `date_from` y `date_to` opcionales en formato ISO
(`YYYY-MM-DD` o datetime ISO). Sin filtros se consulta todo el histórico local.
Una fecha en `date_to` incluye el día completo. Los timestamps no convierten
zonas horarias: se comparan con los datetimes locales almacenados en SQLite.

## Endpoints de reportes

- `GET /api/v1/reports/operational-summary`: ventas, pagos, gastos, estados de
  tickets y cortes, cola de impresión, alertas y existencias negativas.
- `GET /api/v1/reports/sales-by-payment-method`: pagos activos agrupados por
  método.
- `GET /api/v1/reports/sales-by-product`: unidades e importe por producto.
- `GET /api/v1/reports/inventory-consumption`: consumo por insumo; usa
  `SALE_CONSUMPTION` por defecto y acepta `movement_type`.
- `GET /api/v1/reports/print-jobs-summary`: conteos por estado, impresora y tipo
  de trabajo.

Los filtros se aplican al timestamp operativo disponible: `Ticket.paid_at` para
ventas pagadas, `Ticket.cancelled_at` para cancelaciones y `Ticket.created_at`
como respaldo o para estados abiertos; además se usan `Payment.created_at`,
`CashExpense.created_at`, `CashShift.opened_at`, `PrintJob.created_at`,
`StockAlert.opened_at` e `InventoryMovement.created_at`.

## Endpoints de auditoría

- `GET /api/v1/audit/events`: eventos paginados. Acepta `entity_type`,
  `entity_id`, `event_type`, `actor_employee_id`, fechas, `limit` y `offset`.
  `limit` admite de 1 a 500 y `offset` debe ser no negativo.
- `GET /api/v1/audit/tickets/{ticket_id}`: ticket, líneas, pagos, comandas,
  impresiones, movimientos de inventario y eventos.
- `GET /api/v1/audit/cash-shifts/{cash_shift_id}`: corte, resumen calculado,
  tickets, pagos, gastos, impresiones y eventos.

`AuditEvent` no contiene columnas `metadata` o `message`. La respuesta conserva
`before_snapshot`, `after_snapshot` y `reason`; además deriva `metadata.before`
y `metadata.after` cuando los snapshots contienen JSON válido.

## Reglas de cálculo

Se considera venta únicamente un `Ticket` con estado `PAID`. En ventas por
producto se incluyen líneas no canceladas de tipo `SIMPLE` y `PACKAGE_PARENT`.
Las líneas `PACKAGE_COMPONENT` no aportan venta monetaria para evitar duplicar
el precio del paquete.

Se considera pago únicamente un `Payment` con estado `ACTIVE`. Se considera
gasto únicamente un `CashExpense` con estado `ACTIVE`. `net_cash_cents` es
pagos activos menos gastos activos; no representa exclusivamente efectivo
físico por método.

Los insumos con inventario negativo se obtienen agrupando la suma de
`InventoryMovement.signed_quantity_base`. El consumo reporta
`quantity_base`, que es la magnitud positiva del movimiento.

## Auditoría de un ticket completo

La vista por ticket permite contrastar el encabezado y totales con sus líneas,
pagos, comandas por estación y trabajos de impresión. Los movimientos se
relacionan mediante los `ticket_line_id` del ticket. Los eventos incluyen tanto
la referencia directa `ticket_id` como eventos cuya entidad sea el ticket.

## Auditoría de un corte completo

La vista por corte reutiliza `get_cash_shift_summary` y lista sus tickets,
pagos y gastos. Incluye trabajos ligados directamente al corte y trabajos
ligados a cualquiera de sus tickets. Los eventos incluyen referencias directas
al corte y a sus tickets.

## Limitaciones actuales

- No hay conversión de zona horaria ni timestamps timezone-aware.
- Los agregados se calculan en cada consulta; no hay tablas materializadas.
- Tickets históricos sin `paid_at` o `cancelled_at` usan `created_at` como respaldo.
- `net_cash_cents` incluye todos los métodos de pago activos.
- La asociación de inventario a ticket depende de `ticket_line_id`.
- No hay autenticación/autorización específica para estos endpoints todavía.
- No hay Airtable, frontend, gráficos ni exportación PDF/Excel.

## QA

```powershell
$env:DEBUG='false'
uv run pytest
uv run ruff check .
git diff --check
```

Con Uvicorn en `127.0.0.1:8011`:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/reports/operational-summary'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/reports/sales-by-payment-method?date_from=2026-06-01&date_to=2026-06-30'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/reports/sales-by-product'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/reports/inventory-consumption'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/reports/print-jobs-summary'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/audit/events?limit=20&offset=0'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/audit/tickets/1'
Invoke-RestMethod 'http://127.0.0.1:8011/api/v1/audit/cash-shifts/1'
```

## Pendientes

- Hardening pre-sync.
- Reset QA.
- Documentación final.
- Auditoría severa Airtable.
- Sync Airtable.
