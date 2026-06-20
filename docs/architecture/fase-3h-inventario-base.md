# Fase 3-H: inventario base local

## Objetivo

Implementar el ledger local de inventario, recepciones de almacén, ajustes
manuales y alertas de stock bajo. Esta fase no consume inventario por venta, no
envía SMS y no sincroniza Airtable.

## Endpoints

- `GET /api/v1/inventory/items`: insumos con stock calculado.
- `GET /api/v1/inventory/items/{inventory_item_id}/stock`: stock de un insumo.
- `POST /api/v1/inventory/movements`: ajuste manual convertido a unidad base.
- `POST /api/v1/inventory/purchase-receipts`: procesa recepción y gasto opcional.
- `GET /api/v1/inventory/stock-alerts/active`: alertas locales abiertas.

## Servicios

- `inventory_service.py`: stock, conversiones, movimientos y recepciones.
- `stock_alert_service.py`: apertura, actualización y resolución anti-spam.
- Se reutilizan permisos normalizados, folios, corte abierto y gastos de caja.

Los servicios hacen `flush`, pero no `commit`; el límite transaccional vive en
los endpoints o en el proceso llamador.

## Stock actual

`get_current_stock` suma `InventoryMovement.signed_quantity_base`. No existe un
stock editable. La unidad base es `InventoryItem.base_unit_id` y el mínimo es
`InventoryItem.minimum_stock_qty`.

El API normaliza esos nombres como `sku`, `base_unit_id`, `base_unit_name`,
`current_stock`, `stock_minimum` y `stock_status`. `sku` se obtiene de
`InventoryItem.item_code`; `base_unit_name` expone `Unit.unit_key`.

- `current_stock <= 0`: `OUT_OF_STOCK`.
- `0 < current_stock <= minimum_stock`: `LOW_STOCK`.
- `current_stock > minimum_stock`: `OK`.

## Conversión de unidades

`convert_quantity` exige cantidad positiva y unidades existentes/activas. Para
unidades distintas busca primero `UnitConversion` activa en sentido directo; si
solo existe la inversa y su factor es positivo, aplica el recíproco. No hay
factores hardcodeados en el servicio.

El seed incluye KG/G, L/ML y OZ hacia ML/G. Los factores y cantidades operativas
usan `Numeric(18, 6)` para no truncar conversiones decimales.

## Movimientos

Los tipos soportados son `PURCHASE`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`, `WASTE`
y `SALE_CONSUMPTION`. Compras y entradas son positivas; salidas, merma y consumo
son negativas. Todo movimiento exige empleado activo, `INVENTORY_ADJUST`, motivo
y cantidad positiva, genera folio `MOVIMIENTO`, conserva origen y crea el evento
`INVENTORY_MOVEMENT_CREATED`.

El modelo histórico conserva `registered_by_employee_id` como autor y
`unit_cost_cents_snapshot` como costo unitario; el API los expone como
`created_by_employee_id` y `unit_cost_cents`.

## Recepciones y gasto asociado

Una recepción valida todas las líneas antes de persistirlas, convierte cada
cantidad a la unidad base y crea un movimiento `PURCHASE` positivo por línea.
Finaliza en `PROCESSED` y genera `PURCHASE_RECEIPT_PROCESSED`.

Si `paid_amount_cents > 0`, exige corte abierto, permiso `EXPENSE_CREATE` y método
de pago activo. El gasto se crea mediante `create_cash_expense`, queda ligado por
`PurchaseReceipt.cash_expense_id` y participa en la misma transacción. Una
recepción sin pago no requiere corte.

## Alertas locales

Después de cada movimiento se calcula el stock. Si queda bajo o agotado se crea
una única alerta `OPEN`; movimientos posteriores actualizan su cantidad y mensaje
sin duplicarla. Al superar estrictamente el mínimo se marca `RESOLVED`, se fija
`resolved_at` y se genera auditoría. Los eventos son `STOCK_ALERT_OPENED` y
`STOCK_ALERT_RESOLVED`.

## Tablas tocadas

- `inventory_items`, `units`, `unit_conversions`.
- `inventory_movements`.
- `purchase_receipts`, `purchase_receipt_lines`.
- `stock_alerts`.
- `cash_expenses`, `cash_shifts`, `payment_methods`.
- `employees`, roles/permisos, `folio_sequences`, `audit_events`.

La migración `d8b54f902a11` agrega precisión decimal y campos de proveedor,
referencia, nota, origen de movimiento, cantidades/mensaje de alerta.

## Comandos QA

```powershell
$env:DEBUG='false'
uv run alembic upgrade head
uv run python -m app.db.seed
uv run pytest
uv run ruff check .
git diff --check
```

El `DEBUG=false` explícito evita que una variable global de PowerShell con valor
no booleano interfiera con la configuración local.

## Prueba manual en PowerShell

Con Uvicorn activo en `127.0.0.1:8011`:

```powershell
$base = 'http://127.0.0.1:8011/api/v1/inventory'
Invoke-RestMethod "$base/items"

$movement = @{
  employee_id = 1
  inventory_item_id = 1
  movement_type = 'ADJUSTMENT_IN'
  quantity = 500
  unit_id = 1
  reason = 'QA ajuste entrada'
  unit_cost_cents = 10
} | ConvertTo-Json
Invoke-RestMethod "$base/movements" -Method Post -ContentType 'application/json' -Body $movement

$receipt = @{
  employee_id = 1
  supplier_name = 'Proveedor QA'
  invoice_reference = 'FAC-QA-001'
  paid_amount_cents = 0
  note = 'Recepcion QA'
  lines = @(@{inventory_item_id=1; quantity=2; unit_id=2; unit_cost_cents=100})
} | ConvertTo-Json -Depth 4
Invoke-RestMethod "$base/purchase-receipts" -Method Post -ContentType 'application/json' -Body $receipt
Invoke-RestMethod "$base/stock-alerts/active"
```

## Pendientes

- Consumo automático por venta.
- Costo real de venta.
- SMS real opcional.
- Reportes operativos.
- Hardening pre-sync.
- Sync Airtable.
