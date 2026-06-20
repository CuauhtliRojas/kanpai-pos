# Fase 3-G: gastos de caja y cierre de corte

## Objetivo

Esta fase incorpora gastos de caja, un resumen calculado del corte y su cierre
operativo. El cierre persiste el arqueo, registra auditoría y encola una
impresión lógica; no envía trabajos a hardware.

## Endpoints

- `POST /api/v1/pos/cash-expenses`: registra un gasto en el corte abierto.
- `GET /api/v1/pos/cash-shifts/{cash_shift_id}/summary`: calcula ventas, pagos,
  gastos, efectivo esperado, tickets e impresiones pendientes.
- `POST /api/v1/pos/cash-shifts/{cash_shift_id}/close`: valida y cierra el corte.

Los errores de dominio se traducen a `400` para importes inválidos, `403` para
permisos faltantes, `404` para entidades inexistentes y `409` para conflictos
de estado.

## Servicios

- `expense_service.create_cash_expense`: valida el corte abierto, empleado,
  permiso `EXPENSE_CREATE`, datos y método de pago opcional. Genera folio
  `GASTO`, `CashExpense` y `CASH_EXPENSE_CREATED` sin hacer `commit`.
- `cash_shift_service.get_cash_shift_summary`: calcula el resumen directamente
  desde `Ticket`, `Payment`, `PaymentMethod`, `CashExpense` y `PrintJob`.
- `cash_shift_service.close_cash_shift`: exige `CASH_SHIFT_CLOSE`, valida que no
  existan tickets `OPEN` o `IN_PAYMENT`, persiste el arqueo y crea auditoría.
- `print_service.create_cash_shift_print_job`: crea contenido ASCII y un
  `PrintJob` `CORTE` idempotente para la impresora lógica `CAJA`.
- `permission_service`: centraliza la validación de empleado activo y permisos
  normalizados por rol.

## Reglas de gastos

Solo se registra un gasto cuando existe un corte `OPEN`. El monto debe ser
positivo y la descripción no puede quedar vacía. El método de pago es opcional;
si se proporciona debe existir y estar activo. Los gastos efectivos para el
resumen son los de estado `ACTIVE`.

## Reglas del resumen

Las ventas suman `Ticket.total_cents` de tickets `PAID`. Los pagos suman
registros `Payment` `ACTIVE` y se separan por las claves `CASH`, `CARD` y
`TRANSFER`. Los gastos suman `CashExpense` `ACTIVE`.

`expected_cash_cents = opening_cash_cents + total_cash_cents - total_expenses_cents`

El conteo de impresiones pendientes es exacto: `PrintJob` cuenta con
`cash_shift_id`, por lo que no se requiere aproximación por ticket.

## Reglas de cierre

El corte debe estar `OPEN`; los tickets `PAID` y `CANCELLED` no bloquean, pero
los estados `OPEN` e `IN_PAYMENT` sí. Por defecto se permite cerrar con trabajos
de impresión pendientes. Si `allow_pending_print_jobs` es `false`, cualquier
trabajo `PENDING` del corte produce conflicto `409`.

El cierre calcula y persiste efectivo esperado, efectivo declarado y su
diferencia, agrega `CASH_SHIFT_CLOSED` y encola un trabajo `CORTE` con clave
`CORTE:{cash_shift_id}`. Servicio, auditoría e impresión participan en la misma
transacción controlada por el endpoint.

## Migración y tablas

La migración `c31a6b9e2d47_add_cash_shift_closing_fields.py` agrega a
`cash_shifts`:

- `cash_difference_cents`: diferencia declarada menos esperada.
- `closing_note`: nota específica del cierre.

También alinea `cash_expenses` con el contrato de esta fase:

- renombra `expense_type` a `category` y lo vuelve opcional;
- vuelve opcional `payment_method_id`;
- agrega `note`.

Tablas leídas o escritas: `cash_shifts`, `cash_expenses`, `tickets`, `payments`,
`payment_methods`, `print_jobs`, `printers`, `audit_events`, `employees`,
`employee_roles`, `roles`, `role_permissions` y `permissions`.

## QA

Aplicar esquema y ejecutar validaciones:

```powershell
uv run alembic upgrade head
uv run pytest
uv run ruff check .
git diff --check
```

Prueba manual, con Uvicorn en `127.0.0.1:8011` y un corte abierto:

```powershell
$base = "http://127.0.0.1:8011/api/v1/pos"

$expense = @{
  employee_id = 1
  amount_cents = 2500
  description = "Compra servilletas"
  category = "INSUMO"
  payment_method_id = 1
  note = "QA gasto"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/cash-expenses" -ContentType "application/json" -Body $expense

$cashShiftId = 1
Invoke-RestMethod -Method Get -Uri "$base/cash-shifts/$cashShiftId/summary"

$close = @{
  employee_id = 1
  declared_cash_cents = 165000
  note = "Cierre QA"
  allow_pending_print_jobs = $true
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/cash-shifts/$cashShiftId/close" -ContentType "application/json" -Body $close
```

## Pendientes

- inventario por recepciones/venta;
- stock bajo;
- ciclo de impresión física;
- reportes operativos;
- hardening pre-sync;
- sync Airtable.
