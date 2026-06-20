# Cierre del backend local-first

## Estado final antes de Airtable

El backend FastAPI opera sobre SQLite con SQLAlchemy y Alembic. El ciclo POS
local está completo y es verificable sin red: apertura y cierre de caja,
captura y cancelación, comandas lógicas, cobro, inventario, reportes, auditoría
y diagnóstico pre-sync. SQLite es la fuente operativa local; todavía no existe
sincronización ni dependencia de Airtable.

## Módulos y endpoints principales

| Dominio | Capacidades | Endpoints principales |
|---|---|---|
| Sistema | salud y preflight | `GET /health`, `GET /api/v1/preflight/local-backend` |
| Catálogos | productos, categorías, estaciones, pagos | `GET /api/v1/catalog/*` |
| Operación | empleados y mesas | `GET /api/v1/operations/employees`, `GET /api/v1/operations/tables` |
| Caja | apertura, gasto, resumen, cierre | `/api/v1/pos/cash-shifts/*`, `POST /api/v1/pos/cash-expenses` |
| Tickets | apertura, detalle, líneas y cancelación | `/api/v1/pos/tables/{id}/open-ticket`, `/api/v1/pos/tickets/{id}/*` |
| Comandas | envío por ronda y estación | `POST .../send-round`, `GET .../station-orders` |
| Pagos | iniciar cobro, pagos parciales/cierre | `POST .../start-payment`, `/api/v1/pos/tickets/{id}/payments` |
| Impresión | cola, claim, confirmación, fallo y retry | `/api/v1/printing/jobs/*` |
| Inventario | stock, movimientos, compras y alertas | `/api/v1/inventory/*` |
| Reportes | resumen, ventas, consumo e impresión | `/api/v1/reports/*` |
| Auditoría | eventos, ticket y corte completos | `/api/v1/audit/*` |

## Tablas principales por dominio

- Catálogos y seguridad: `products`, `menu_categories`, `production_stations`,
  `printers`, `payment_methods`, `employees`, `roles`, `permissions`,
  `employee_roles`, `role_permissions`, `units`, `inventory_items`,
  `product_recipes` y `folio_sequences`.
- Caja y venta: `cash_shifts`, `cash_expenses`, `tickets`, `ticket_lines`,
  `ticket_line_notes`, `ticket_discounts`, `payments` y
  `table_status_events`.
- Comandas e impresión: `command_batches`, `station_orders`,
  `station_order_lines` y `print_jobs`.
- Inventario: `inventory_movements`, `purchase_receipts`,
  `purchase_receipt_lines` y `stock_alerts`.
- Trazabilidad: `audit_events`.

## Reglas consolidadas

- Solo puede existir un corte `OPEN` y toda venta pertenece a un corte.
- Una mesa solo puede tener un ticket activo; su cache transita entre `FREE`,
  `OCCUPIED` e `IN_PAYMENT` y se libera al pagar o cancelar.
- Solo líneas capturadas se envían en una nueva ronda; la comanda se divide por
  estación y encola snapshots idempotentes para impresión.
- El cobro requiere líneas enviadas y total positivo. Los pagos activos pueden
  ser parciales; al cubrir el total el ticket pasa a `PAID` dentro de la misma
  transacción que inventario, mesa, auditoría e impresión de cuenta.
- Cancelaciones conservan trazabilidad, requieren actor/razón y anulan los
  pagos activos correspondientes.
- El consumo de inventario deriva de recetas, registra movimientos
  `SALE_CONSUMPTION` con origen y se ejecuta una sola vez por ticket pagado.
- Reportes consideran ventas `PAID`, pagos/gastos `ACTIVE` y excluyen líneas
  canceladas o componentes monetarios duplicados de paquetes.

## Invariantes críticas

Antes de cualquier diseño de sync deben mantenerse: esquema crítico
consultable, seed mínimo completo, máximo un corte abierto, máximo un ticket
activo por mesa, consumo de inventario para tickets pagados con receta, ningún
pago activo en ticket cancelado, todos los trabajos con snapshot de impresora
y todos los movimientos de venta con `source_type`.

El endpoint y `scripts/check_pre_sync_invariants.py` son la definición única de
estos checks. `scripts/reset_operational_data.py --yes` permite recuperar una
base QA limpia sin alterar catálogos.

## Fuera del cierre local-first

No se incluyen autenticación remota, frontend, hardware ESC/POS, operación
multi-sucursal, alta disponibilidad, exportaciones, Airtable ni sincronización.
Los timestamps continúan siendo locales y sin zona horaria; los reportes se
calculan en consulta y la cola implementada es lógica, no impresión física.

## Auditoría severa de Airtable

La siguiente fase debe inventariar bases, tablas, campos, tipos, relaciones,
IDs estables, duplicados, estados, volúmenes, revisiones, permisos y calidad de
datos del Airtable existente. También debe comparar sus catálogos contra el
modelo SQLite, identificar transformaciones y definir propiedad de cada dato,
idempotencia, watermarks, reintentos, conflictos, borrados y observabilidad.

## Qué no hacer todavía

No crear ni modificar tablas de Airtable, no reutilizar una estructura remota
sin auditarla, no agregar credenciales, SDKs o llamadas HTTP, no poblar tablas
de sync, no implementar pull/push y no conectar el daemon físico de impresión.

## Orden recomendado

1. Auditoría del Airtable actual.
2. Diseño de un Airtable limpio.
3. Pull de catálogos Airtable → SQLite.
4. Push de transacciones SQLite → Airtable.
5. Daemon de impresión física ESC/POS.
