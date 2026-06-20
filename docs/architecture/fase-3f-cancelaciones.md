# Fase 3-F: cancelaciones

## Objetivo

Esta fase incorpora cancelación transaccional de líneas y tickets. Las operaciones
requieren un empleado activo con el permiso `TICKET_CANCEL`, registran auditoría y
dejan el `commit` o `rollback` al endpoint llamador.

Los estados usados son los existentes en el backend:

- Ticket: `OPEN`, `IN_PAYMENT`, `PAID`, `CANCELLED`.
- Línea: `CAPTURED`, `ENVIADO_COMANDA`, `IMPRESO`, `CANCELLED`.
- Pago: `ACTIVE`, `CANCELLED`.

No se añadieron estados ni migraciones.

## Endpoints

- `POST /api/v1/pos/ticket-lines/{line_id}/cancel`
- `POST /api/v1/pos/tickets/{ticket_id}/cancel`

Ambos reciben `employee_id` y un `reason` opcional. La cancelación de línea
devuelve la línea, el ticket recalculado y el número de trabajos de impresión.
La cancelación de ticket devuelve conteos de líneas, pagos y trabajos cancelados,
además de indicar si la mesa quedó libre.

## Servicios

- `cancellation_service.py`: aplica reglas de cancelación, pagos, auditoría y
  coordinación de comandas.
- `permission_service.py`: resuelve permisos activos a través de `EmployeeRole`,
  `Role`, `RolePermission` y `Permission`.
- `print_service.py`: crea trabajos `CANCELACION_COMANDA` ASCII e idempotentes.
- `ticket_service.py`: centraliza el recálculo de totales cobrables.
- `table_service.py`: libera la mesa y crea `TableStatusEvent` por cancelación.

El seed ya define `TICKET_CANCEL` y lo asigna de forma idempotente a `ADMIN` y
`GERENTE`. El empleado administrador seed pertenece a `ADMIN`.

## Cancelación de línea

Una línea `CAPTURED` cambia a `CANCELLED`, guarda empleado, motivo y fecha,
recalcula el ticket y crea `TICKET_LINE_CANCELLED`; no genera impresión.

Una línea `ENVIADO_COMANDA` o `IMPRESO` hace lo mismo y, si tiene estación,
encola una `CANCELACION_COMANDA`. El contenido incluye negocio, folio, estación,
producto, cantidad y motivo. Su clave es `CANCEL_LINE:{ticket_line_id}`.

No se permite cancelar líneas de tickets pagados o cancelados, ni repetir una
cancelación.

## Paquetes y combos

Una línea `PACKAGE_COMPONENT` no puede cancelarse directamente mientras su padre
siga activo; se debe cancelar `PACKAGE_PARENT`. Al cancelar el padre también se
cancelan todos sus componentes activos. El recálculo elimina únicamente el precio
del padre porque los componentes tienen precio incluido. Cada componente ya
enviado con estación genera su propia cancelación de comanda; el padre no genera
una comanda adicional.

## Cancelación de ticket

Solo se cancelan tickets `OPEN` o `IN_PAYMENT`. Todas sus líneas activas pasan a
`CANCELLED`, y cada línea enviada con estación genera un trabajo con clave
`CANCEL_TICKET:{ticket_id}:LINE:{ticket_line_id}`.

Los pagos `ACTIVE` cambian a `CANCELLED` y guardan empleado, motivo y fecha. El
ticket cambia a `status=CANCELLED` y `payment_status=CANCELLED`, conserva sus
totales como evidencia histórica y registra `TICKET_CANCELLED`. La mesa pasa a
`FREE` mediante un `TableStatusEvent` que conserva el estado previo real.

## Tablas tocadas

- `tickets`
- `ticket_lines`
- `payments`
- `print_jobs`
- `dining_tables`
- `table_status_events`
- `audit_events`
- Lectura de `employees`, `employee_roles`, `roles`, `role_permissions`,
  `permissions`, `production_stations`, `printers`, `station_orders` y
  `station_order_lines`.

## QA

```powershell
$env:DEBUG = "false"
uv run pytest
uv run ruff check .
git diff --check
```

Con Uvicorn ejecutándose en `127.0.0.1:8011`, ejemplos PowerShell:

```powershell
$body = @{ employee_id = 1; reason = "Error de captura" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8011/api/v1/pos/ticket-lines/1/cancel" `
  -ContentType "application/json" -Body $body

$body = @{ employee_id = 1; reason = "Cliente cancelo pedido" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8011/api/v1/pos/tickets/1/cancel" `
  -ContentType "application/json" -Body $body
```

Equivalentes con curl:

```bash
curl -X POST http://127.0.0.1:8011/api/v1/pos/ticket-lines/1/cancel \
  -H "Content-Type: application/json" \
  -d '{"employee_id":1,"reason":"Error de captura"}'

curl -X POST http://127.0.0.1:8011/api/v1/pos/tickets/1/cancel \
  -H "Content-Type: application/json" \
  -d '{"employee_id":1,"reason":"Cliente cancelo pedido"}'
```

## Pendientes

- Cierre de corte.
- Gastos de caja.
- Inventario por venta.
- Impresión física real.
- Sincronización con Airtable.
