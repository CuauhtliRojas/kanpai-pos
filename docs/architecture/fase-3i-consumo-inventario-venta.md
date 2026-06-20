# Fase 3-I: consumo de inventario por venta

## Objetivo

Descontar automáticamente los insumos configurados en `ProductRecipe` cuando
un ticket queda totalmente pagado, dentro de la misma transacción que cierra la
venta. Los productos sin receta se consideran válidos y no generan consumo.

Las recetas `DEV-CHELA` (100 ML de `INV-SAKE`) y `DEV-SAKE` (120 ML de
`INV-SAKE`) son datos temporales de QA; no representan recetas comerciales.
El stock de prueba debe ingresarse mediante recepción o movimiento, nunca en el
seed.

## Momento del consumo

El consumo ocurre únicamente cuando el pago acumulado cubre el total y el
ticket cambia a `PAID`. No ocurre al capturar productos, enviar una ronda,
iniciar el cobro ni registrar un pago parcial. Un ticket cancelado tampoco puede
consumir inventario.

No se descuenta al enviar ronda porque una comanda representa intención de
producción, no una venta consolidada: todavía puede cancelarse o modificarse.
Esta fase usa el pago completo como evento contable estable.

El orden transaccional del cierre es:

1. Marcar ticket como `PAID`.
2. Generar movimientos y marcar `inventory_consumed_at`.
3. Liberar la mesa y registrar auditoría.
4. Crear el `PrintJob` lógico `TICKET`.

Un error técnico revierte pago, estado, movimientos, alertas, impresión y mesa.

## Reglas de líneas y recetas

- `SIMPLE`: consume la receta activa del producto de la línea.
- `PACKAGE_COMPONENT`: consume las recetas de cada componente y respeta la
  cantidad expandida al capturar el paquete.
- `PACKAGE_PARENT`: cobra el paquete, pero no consume inventario.
- `CANCELLED` (incluidos equivalentes históricos): no consume.
- Producto sin receta activa: se omite sin impedir el cierre.

Por cada receta se calcula:

`line.quantity * recipe.quantity_base * (1 + recipe.waste_pct / 100)`

El movimiento tiene tipo `SALE_CONSUMPTION`, cantidad firmada negativa,
`ticket_line_id`, `source_type = TICKET_LINE`, `source_id = ticket_line.id` y
motivo `Venta ticket {folio}`.

## Idempotencia y stock bajo

`Ticket.inventory_consumed_at` es la marca idempotente. Si ya tiene valor, una
nueva invocación no genera movimientos. La marca se escribe después de procesar
todas las recetas y dentro de la transacción de pago.

El stock puede quedar negativo y no bloquea la venta. Cada movimiento reutiliza
la evaluación local de stock: abre o actualiza una sola alerta activa cuando el
stock está en/bajo el mínimo, y movimientos futuros de entrada la resuelven al
superar el mínimo.

## Consulta

`GET /api/v1/pos/tickets/{ticket_id}/inventory-movements`

Devuelve movimientos `SALE_CONSUMPTION` cuyo origen es una línea del ticket. Un
ticket existente sin consumo devuelve una lista vacía; uno inexistente devuelve
404.

## Tablas tocadas

- `tickets`: nuevo `inventory_consumed_at`.
- `ticket_lines`: origen y reglas de elegibilidad.
- `product_recipes`: cantidades y merma configuradas.
- `inventory_items`: costo snapshot, unidad base y mínimo.
- `inventory_movements`: ledger negativo de venta.
- `stock_alerts`: alerta local abierta, actualizada o resuelta.
- `print_jobs` y `table_status_events`: permanecen en el cierre transaccional.

## QA local en PowerShell

Con la API que el operador mantiene en `127.0.0.1:8011`:

```powershell
$ticketId = 1
Invoke-RestMethod "http://127.0.0.1:8011/api/v1/pos/tickets/$ticketId/inventory-movements"
```

Para validar esquema, seed y calidad desde la raíz:

```powershell
$env:DEBUG = "false" # solo si el entorno heredado no contiene un booleano válido
uv run alembic upgrade head
uv run python -m app.db.seed
uv run pytest
uv run ruff check .
git diff --check
```

Para cargar stock QA use `POST /api/v1/inventory/movements` con
`ADJUSTMENT_IN`, o `POST /api/v1/inventory/purchase-receipts`.

## Pendientes

- Costeo avanzado y criterios de redondeo financiero.
- Reportes operativos de consumo y desviaciones.
- Impresión física real.
- Hardening pre-sync, incluida concurrencia entre procesos.
- Sincronización con Airtable.
