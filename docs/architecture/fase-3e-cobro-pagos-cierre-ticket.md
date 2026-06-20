# Fase 3-E: cobro, pagos y cierre de ticket

## Objetivo

Iniciar el cobro de tickets con rondas enviadas, registrar pagos parciales o
completos y cerrar de forma transaccional un ticket pagado. Esta fase no mueve
inventario, no imprime físicamente y no sincroniza con Airtable.

Los estados canónicos del backend son `OPEN`, `IN_PAYMENT`, `PAID` y
`CANCELLED`. El mapeo conceptual con Airtable es:

- Airtable `ABIERTO` equivale a backend `OPEN`.
- Airtable `EN_COBRO` equivale a backend `IN_PAYMENT`.
- Airtable `COBRADO` equivale a backend `PAID`.
- Airtable `CANCELADO` equivale a backend `CANCELLED`.

## Endpoints

- `POST /api/v1/pos/tickets/{ticket_id}/start-payment`: inicia cobro.
- `POST /api/v1/pos/tickets/{ticket_id}/payments`: registra un pago.
- `GET /api/v1/pos/tickets/{ticket_id}/payments`: devuelve pagos activos y
  cancelados, total activo pagado, saldo restante y estado de cierre.

## Servicios

`app/services/payment_service.py` incorpora `start_payment`, `create_payment`,
`list_ticket_payments` y `get_active_payment_total`. Los servicios no hacen
`commit`; la ruta confirma o revierte la operación completa.

`print_service.py` crea el trabajo lógico final y `table_service.py` libera la
mesa y registra su cambio de estado.

## Reglas de iniciar cobro

El ticket y el empleado activo deben existir. El ticket debe estar `OPEN`, tener
al menos una línea no cancelada, total positivo y ninguna línea `CAPTURED`.
Al iniciar cambia a `IN_PAYMENT`, registra `billing_started_at`, actualiza la
mesa a `IN_PAYMENT` y crea el evento `PAYMENT_STARTED`.

## Pago parcial

El ticket debe estar `IN_PAYMENT`; el método debe existir y estar activo. El
monto es positivo, los métodos configurados exigen referencia y el efectivo
recibido, cuando se informa, no puede ser menor al monto. Un pago parcial queda
`ACTIVE`, mantiene ticket y mesa en `IN_PAYMENT`, y crea `PAYMENT_REGISTERED`.

## Pago completo

Cuando la suma de pagos `ACTIVE` alcanza o supera el total, se comprueba otra
vez que no haya líneas `CAPTURED`. El ticket cambia a `PAID`, su
`payment_status` cambia a `PAID`, se registran `paid_at` y el empleado de cierre,
y se crea `TICKET_PAID`.

La mesa cambia de `IN_PAYMENT` a `FREE` y se persiste un `TableStatusEvent` con
esa transición.

## PrintJob tipo TICKET

El cierre crea un único trabajo con impresora lógica `CAJA`, tipo `TICKET`,
estado `PENDING`, cero intentos e idempotencia `TICKET:{ticket_id}`. Su snapshot
ASCII contiene negocio, tipo, folio, mesa, total, pagos y agradecimiento. La
impresión física queda fuera de esta fase.

## Tablas tocadas

- `tickets`
- `ticket_lines` (solo lectura de validación)
- `payments`
- `payment_methods` (solo lectura)
- `dining_tables`
- `table_status_events`
- `audit_events`
- `print_jobs`
- `printers` y `folio_sequences` (resolución y folios)

## QA

```powershell
uv run pytest
uv run ruff check .
git diff --check
```

## Curl de prueba

```powershell
curl.exe -X POST http://127.0.0.1:8011/api/v1/pos/tickets/1/start-payment `
  -H "Content-Type: application/json" `
  -d '{"employee_id":1}'

curl.exe -X POST http://127.0.0.1:8011/api/v1/pos/tickets/1/payments `
  -H "Content-Type: application/json" `
  -d '{"employee_id":1,"payment_method_id":1,"amount_cents":14000,"received_cents":20000,"reference":null}'

curl.exe http://127.0.0.1:8011/api/v1/pos/tickets/1/payments
```

## Pendientes

- Inventario por venta.
- Cancelaciones.
- Cierre de corte.
- Impresión física real.
- Sync Airtable.
