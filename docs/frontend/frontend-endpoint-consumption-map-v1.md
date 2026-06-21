# Mapa de Consumo de Endpoints Frontend V1 — Kanpai POS

## 1. Propósito

Este documento mapea los endpoints del Backend V1 contra funciones de frontend. Su objetivo es evitar que el frontend invente contratos, duplique reglas de negocio o consuma servicios externos directamente.

La fuente de verdad contractual es `GET /openapi.json` del backend local.

## 2. Reglas de consumo

- Toda llamada debe pasar por `src/api/http.ts`.
- Cada dominio debe tener su archivo `features/<dominio>/api/*Api.ts`.
- Los hooks de TanStack Query deben vivir en `features/<dominio>/hooks`.
- Las mutaciones deben invalidar query keys relacionadas.
- Los errores `400`, `403`, `404` y `409` deben mostrarse como errores operativos, no como fallas técnicas genéricas.
- Los errores de conexión deben indicar que FastAPI local no está levantado.
- El frontend no debe llamar Airtable.
- El frontend no debe manipular SQLite.
- El frontend no debe calcular totales finales cuando el backend los devuelve.

## 3. System

| Endpoint                                 |     Tipo | Uso UI                               | Fase       |
| ---------------------------------------- | -------: | ------------------------------------ | ---------- |
| `GET /health`                            |    Query | Health backend local                 | Foundation |
| `GET /api/v1/system/db`                  |    Query | Estado SQLite                        | Sistema    |
| `GET /api/v1/system/seed-summary`        |    Query | Diagnóstico catálogo base            | Sistema    |
| `GET /api/v1/system/business-settings`   |    Query | Política fiscal/configuración activa | Sistema    |
| `GET /api/v1/system/airtable-sync`       |    Query | Semáforo sync + detalle admin        | Foundation |
| `POST /api/v1/system/airtable-sync/pull` | Mutation | Pull manual Airtable → SQLite        | Admin      |
| `POST /api/v1/system/airtable-sync/push` | Mutation | Push manual SQLite → Airtable        | Admin      |
| `POST /api/v1/system/airtable-sync/run`  | Mutation | Ciclo completo manual                | Admin      |

Notas:

- Los POST de sync deben usar confirmación explícita.
- Pull durante operación activa debe mostrarse como acción riesgosa.
- El topbar solo muestra semáforo; el detalle vive en pantalla de sistema.

## 4. Auth y sesión

| Endpoint                      |     Tipo | Uso UI                   | Fase |
| ----------------------------- | -------: | ------------------------ | ---- |
| `POST /api/v1/auth/login-pin` | Mutation | Login por empleado + PIN | Auth |
| `GET /api/v1/auth/me`         |    Query | Resolver sesión activa   | Auth |
| `POST /api/v1/auth/logout`    | Mutation | Cerrar sesión            | Auth |

Modelo frontend:

```text
session_token
employee.id
employee.employee_code
employee.full_name
employee.pos_alias
expires_at
```

Reglas:

- El topbar muestra `pos_alias` si existe; si no, `full_name`.
- Las acciones operativas usan `employee.id`.
- Si la sesión expira, bloquear operación y volver a login.
- No inventar roles si el backend no los devuelve en `me`.
- Implementado en sesión V1: `me` usa el header `X-Kanpai-Session`; el PIN no se persiste y los permisos devueltos quedan reservados para fase 3.

## 5. Operaciones base

| Endpoint                           |  Tipo | Uso UI                   | Fase       |
| ---------------------------------- | ----: | ------------------------ | ---------- |
| `GET /api/v1/operations/employees` | Query | Selector/lista empleados | Auth/Admin |
| `GET /api/v1/operations/tables`    | Query | Grid de mesas            | POS        |

Reglas:

- La grilla de mesas debe refrescar tras abrir/cerrar/cobrar/cancelar ticket.
- No agregar producto sin mesa/ticket activo.

## 6. Catálogo POS

| Endpoint                                                   |  Tipo | Uso UI                   | Fase       |
| ---------------------------------------------------------- | ----: | ------------------------ | ---------- |
| `GET /api/v1/catalog/categories`                           | Query | Filtros de productos     | POS        |
| `GET /api/v1/catalog/products`                             | Query | Grid de productos        | POS        |
| `GET /api/v1/catalog/payment-methods`                      | Query | Botones de cobro         | Pago       |
| `GET /api/v1/catalog/stations`                             | Query | Filtros producción/admin | Producción |
| `GET /api/v1/catalog/variant-groups`                       | Query | Catálogo de variantes    | POS        |
| `GET /api/v1/catalog/products/{product_id}/variant-groups` | Query | Variantes de producto    | POS        |

Reglas:

- El frontend solo muestra productos activos/visibles según respuesta backend.
- La edición fuerte de catálogo no vive en POS.

## 7. Caja / cortes

| Endpoint                                              |     Tipo | Uso UI                | Fase |
| ----------------------------------------------------- | -------: | --------------------- | ---- |
| `GET /api/v1/pos/cash-shifts/current`                 |    Query | Resolver corte activo | Caja |
| `POST /api/v1/pos/cash-shifts/open`                   | Mutation | Abrir corte           | Caja |
| `GET /api/v1/pos/cash-shifts/{cash_shift_id}/summary` |    Query | Resumen corte         | Caja |
| `POST /api/v1/pos/cash-shifts/{cash_shift_id}/close`  | Mutation | Cerrar corte          | Caja |
| `POST /api/v1/pos/cash-expenses`                      | Mutation | Registrar gasto       | Caja |

Invalidaciones sugeridas:

```text
cashShift.current
cashShift.summary
reports.operationalSummary
printing.pendingJobs
```

Reglas:

- Si no hay corte abierto, POS queda bloqueado.
- Cierre de corte debe mostrar pendientes de impresión si existen.
- Monto de apertura/cierre se captura en pesos pero se envía como centavos.

## 8. Mesas y tickets

| Endpoint                                         |     Tipo | Uso UI                  | Fase                 |
| ------------------------------------------------ | -------: | ----------------------- | -------------------- |
| `POST /api/v1/pos/tables/{table_id}/open-ticket` | Mutation | Abrir ticket para mesa  | POS                  |
| `GET /api/v1/pos/tickets/{ticket_id}`            |    Query | Ticket activo           | POS                  |
| `GET /api/v1/pos/tickets/{ticket_id}/lines`      |    Query | Líneas de ticket        | POS                  |
| `POST /api/v1/pos/tickets/{ticket_id}/lines`     | Mutation | Agregar producto        | POS                  |
| `POST /api/v1/pos/ticket-lines/{line_id}/modify` | Mutation | Modificar nota de línea | POS                  |
| `POST /api/v1/pos/ticket-lines/{line_id}/cancel` | Mutation | Cancelar línea          | POS                  |
| `POST /api/v1/pos/tickets/{ticket_id}/cancel`    | Mutation | Cancelar ticket         | Admin/POS autorizado |

Invalidaciones sugeridas:

```text
tables.list
ticket.detail(ticketId)
ticket.lines(ticketId)
ticket.payments(ticketId)
ticket.stationOrders(ticketId)
cashShift.summary
printing.pendingJobs
```

Reglas:

- Cancelar línea/ticket exige confirmación.
- El backend decide permisos y conflictos.
- El frontend no recalcula total del ticket.

## 9. Rondas y comandas

| Endpoint                                             |     Tipo | Uso UI                 | Fase      |
| ---------------------------------------------------- | -------: | ---------------------- | --------- |
| `POST /api/v1/pos/tickets/{ticket_id}/send-round`    | Mutation | Enviar ronda/comanda   | POS       |
| `GET /api/v1/pos/tickets/{ticket_id}/station-orders` |    Query | Ver comandas de ticket | POS/Admin |

Invalidaciones sugeridas:

```text
ticket.lines(ticketId)
ticket.stationOrders(ticketId)
printing.pendingJobs
production.stationOrders
```

Reglas:

- Botón “ENVIAR RONDA” solo aparece si hay líneas pendientes.
- Si impresión falla, el estado debe verse en cola de impresión.

## 10. Pagos

| Endpoint                                             |     Tipo | Uso UI           | Fase |
| ---------------------------------------------------- | -------: | ---------------- | ---- |
| `POST /api/v1/pos/tickets/{ticket_id}/start-payment` | Mutation | Iniciar cobro    | Pago |
| `GET /api/v1/pos/tickets/{ticket_id}/payments`       |    Query | Resumen de pagos | Pago |
| `POST /api/v1/pos/tickets/{ticket_id}/payments`      | Mutation | Registrar pago   | Pago |

Invalidaciones sugeridas:

```text
ticket.detail(ticketId)
ticket.payments(ticketId)
tables.list
cashShift.summary
reports.salesByPaymentMethod
printing.pendingJobs
```

Reglas:

- El backend devuelve `remaining_cents` y `closed`.
- El frontend no decide si el ticket queda cerrado.
- En efectivo, `received_cents` puede generar `change_cents`.

## 11. Cuentas divididas

| Endpoint                                               |     Tipo | Uso UI             | Fase          |
| ------------------------------------------------------ | -------: | ------------------ | ------------- |
| `GET /api/v1/pos/tickets/{ticket_id}/splits`           |    Query | Ver divisiones     | Pago avanzado |
| `POST /api/v1/pos/tickets/{ticket_id}/splits/equal`    | Mutation | Dividir por partes | Pago avanzado |
| `POST /api/v1/pos/tickets/{ticket_id}/splits/by-lines` | Mutation | Dividir por líneas | Pago avanzado |
| `POST /api/v1/pos/ticket-splits/{split_id}/payments`   | Mutation | Pagar split        | Pago avanzado |

Reglas:

- No entra en POS inicial.
- Debe ocultarse detrás de acción secundaria para no estorbar cobro simple.

## 12. Impresión

| Endpoint                                            |     Tipo | Uso UI                 | Fase                 |
| --------------------------------------------------- | -------: | ---------------------- | -------------------- |
| `GET /api/v1/printing/printers`                     |    Query | Ver impresoras lógicas | Admin                |
| `GET /api/v1/printing/jobs/pending`                 |    Query | Cola pendiente         | Admin/Soporte        |
| `GET /api/v1/printing/jobs/{print_job_id}`          |    Query | Detalle trabajo        | Admin/Soporte        |
| `POST /api/v1/printing/jobs/retry-failed`           | Mutation | Reintentar fallidos    | Admin                |
| `POST /api/v1/printing/jobs/{print_job_id}/reprint` | Mutation | Reimprimir con motivo  | Admin/POS autorizado |
| `POST /api/v1/printing/jobs/claim-next`             | Mutation | Worker impresión       | Worker               |
| `POST /api/v1/printing/jobs/{print_job_id}/printed` | Mutation | Worker marca impreso   | Worker               |
| `POST /api/v1/printing/jobs/{print_job_id}/failed`  | Mutation | Worker marca fallido   | Worker               |

Reglas:

- El POS puede mostrar alerta de impresión, pero no debe convertirse en worker.
- Worker físico de impresión debe seguir siendo proceso separado.
- Reimpresión requiere empleado y motivo.

## 13. Producción

| Endpoint                                                             |     Tipo | Uso UI                         | Fase       |
| -------------------------------------------------------------------- | -------: | ------------------------------ | ---------- |
| `GET /api/v1/production/station-orders`                              |    Query | Vista de comandas por estación | Producción |
| `POST /api/v1/production/station-orders/{station_order_id}/receive`  | Mutation | Recibir comanda                | Producción |
| `POST /api/v1/production/station-orders/{station_order_id}/start`    | Mutation | Iniciar preparación            | Producción |
| `POST /api/v1/production/station-orders/{station_order_id}/complete` | Mutation | Completar preparación          | Producción |
| `POST /api/v1/production/station-orders/{station_order_id}/deliver`  | Mutation | Entregar                       | Producción |

Reglas:

- Pantalla secundaria/respaldo, no reemplazo obligatorio de comandas físicas.
- Debe filtrar por estación si hay estación activa.

## 14. Inventario

| Endpoint                                                |     Tipo | Uso UI             | Fase                       |
| ------------------------------------------------------- | -------: | ------------------ | -------------------------- |
| `GET /api/v1/inventory/items`                           |    Query | Lista insumos      | Admin                      |
| `GET /api/v1/inventory/items/{inventory_item_id}/stock` |    Query | Stock detalle      | Admin                      |
| `GET /api/v1/inventory/stock-alerts/active`             |    Query | Alertas stock bajo | Admin/Topbar alerta futura |
| `POST /api/v1/inventory/movements`                      | Mutation | Movimiento manual  | Admin                      |
| `POST /api/v1/inventory/purchase-receipts`              | Mutation | Recepción compra   | Admin                      |

Reglas:

- No debe mezclarse con POS rápido.
- Alertas críticas pueden mostrarse como indicador compacto, no como bloqueo.

## 15. Reportes

| Endpoint                                      |  Tipo | Uso UI              | Fase     |
| --------------------------------------------- | ----: | ------------------- | -------- |
| `GET /api/v1/reports/operational-summary`     | Query | Dashboard gerencial | Reportes |
| `GET /api/v1/reports/sales-by-product`        | Query | Ventas producto     | Reportes |
| `GET /api/v1/reports/sales-by-payment-method` | Query | Ventas método pago  | Reportes |
| `GET /api/v1/reports/inventory-consumption`   | Query | Consumo inventario  | Reportes |
| `GET /api/v1/reports/production-times`        | Query | Tiempos producción  | Reportes |
| `GET /api/v1/reports/print-jobs-summary`      | Query | Salud impresión     | Reportes |

Reglas:

- Reportes no deben vivir en navegación visible permanente.
- Fechas deben ser filtros claros, no inputs frágiles.

## 16. Auditoría

| Endpoint                                        |  Tipo | Uso UI             | Fase      |
| ----------------------------------------------- | ----: | ------------------ | --------- |
| `GET /api/v1/audit/events`                      | Query | Bitácora filtrable | Auditoría |
| `GET /api/v1/audit/tickets/{ticket_id}`         | Query | Auditoría ticket   | Auditoría |
| `GET /api/v1/audit/cash-shifts/{cash_shift_id}` | Query | Auditoría corte    | Auditoría |

Reglas:

- Auditoría es consulta; no modifica operación.
- Debe estar protegida por permisos.
