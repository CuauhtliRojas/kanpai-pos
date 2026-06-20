# Casos de uso de endpoints

## Fase 3-M

- `GET /api/v1/production/station-orders`: filtros de estación, estado y fecha; incluye líneas.
- `POST /api/v1/production/station-orders/{id}/receive|start|complete|deliver`: transición estricta con empleado, timestamp y auditoría.
- `GET /api/v1/reports/production-times`: promedios de recepción, preparación y servicio por estación.
- `POST /api/v1/pos/ticket-lines/{line_id}/modify`: registra nota y, si ya fue enviada, encola `Modificacion`.
- `POST|GET /api/v1/pos/tickets/{ticket_id}/discounts`: aplica/lista descuentos y cortesías autorizados.
- `GET /api/v1/system/business-settings`: expone la política fiscal activa.
- `GET /api/v1/printing/jobs/{id}` y `POST /api/v1/printing/jobs/{id}/reprint`: inspección y reimpresión auditada.

Producción sigue `En cola` → `Recibida` → `En preparacion` → `Terminada` → `Entregada`. `Cancelada` es terminal.

Fuente: router y `app.openapi()` reales al 2026-06-19. Base URL: `http://127.0.0.1:8011`. En los ejemplos se omiten campos de respuesta no esenciales. Los errores de negocio usan `{"detail":"mensaje"}` y normalmente son 400, 403, 404 o 409; 422 corresponde a validación FastAPI.

## System / health

### GET /health

Uso: confirmar que el proceso HTTP responde. Actor: frontend o supervisor local. Precondiciones: proceso iniciado. Payload: ninguno. Respuesta: `{"status":"ok"}`. Errores: 500 si falla la aplicación. Efectos DB: ninguno. Siguiente: `GET /api/v1/system/db`.

### GET /api/v1/system/db

Uso: verificar conectividad SQLite. Actor: frontend administrativo. Precondiciones: archivo accesible. Payload: ninguno. Respuesta: `{"database":"ok"}`. Errores: 500 por conexión. Efectos DB: lectura trivial. Siguiente: `GET /api/v1/system/seed-summary`.

### GET /api/v1/system/seed-summary

Uso: contar catálogos mínimos. Actor: gerente/soporte. Precondiciones: DB disponible. Payload: ninguno. Respuesta: `{"tables":21,"categories":7,"stations":4,"payment_methods":3}`. Errores: 500. Efectos DB: lecturas de catálogos. Siguiente: `GET /api/v1/preflight/local-backend`.

## Catalog

### GET /api/v1/catalog/products

Uso: listar productos activos visibles para captura. Actor: cajero. Precondiciones: seed/catálogo cargado. Payload: ninguno. Respuesta: `[{"id":1,"sku":"DEV-CHELA","product_type":"Simple","display_name":"Chela desarrollo","price_cents":7000}]`. Errores: 500. Efectos DB: lectura. Siguiente: `POST /api/v1/pos/tickets/{ticket_id}/lines`.

### GET /api/v1/catalog/categories

Uso: construir filtros del menú. Actor: cajero. Precondiciones: catálogo cargado. Payload: ninguno. Respuesta: `[{"id":1,"name":"Yakitori","sort_order":1}]`. Errores: 500. Efectos DB: lectura. Siguiente: `GET /api/v1/catalog/products`.

### GET /api/v1/catalog/stations

Uso: mostrar estaciones lógicas de producción. Actor: frontend administrativo. Precondiciones: catálogo cargado. Payload: ninguno. Respuesta: `[{"id":1,"station_key":"COCINA","name":"Cocina","printer_key":"COCINA"}]`. Errores: 500. Efectos DB: lectura. Siguiente: preflight o captura.

### GET /api/v1/catalog/payment-methods

Uso: listar métodos aceptados. Actor: cajero. Precondiciones: seed cargado. Payload: ninguno. Respuesta: `[{"id":1,"method_key":"Efectivo","name":"Efectivo","requires_reference":false}]`. Errores: 500. Efectos DB: lectura. Siguiente: `POST /api/v1/pos/tickets/{ticket_id}/payments`.

## Operations

### GET /api/v1/operations/tables

Uso: listar mesas y estado actual. Actor: cajero. Precondiciones: mesas sembradas. Payload: ninguno. Respuesta: `[{"id":1,"display_name":"Mesa 2","status_cache":"Libre","active":true}]`. Errores: 500. Efectos DB: lectura. Siguiente: `POST /api/v1/pos/tables/{table_id}/open-ticket`.

### GET /api/v1/operations/employees

Uso: seleccionar empleado activo. Actor: cajero/gerente. Precondiciones: empleados cargados. Payload: ninguno. Respuesta: `[{"id":1,"employee_code":"EMP-0001","full_name":"Administrador"}]`. Errores: 500. Efectos DB: lectura. Siguiente: abrir corte o ticket.

## POS: cortes y gastos

### POST /api/v1/pos/cash-shifts/open

Uso: abrir el corte operativo único. Actor: cajero/gerente. Precondiciones: empleado activo con permiso y ningún corte abierto. Payload: `{"employee_id":1,"opening_cash_cents":100000}`. Respuesta: `{"id":1,"folio":"CC000001","status":"Abierto"}`. Errores: 403 sin permiso, 404 empleado, 409 corte existente. Efectos DB: crea corte y evento `Corte abierto`. Siguiente: `GET /api/v1/operations/tables`.

### GET /api/v1/pos/cash-shifts/current

Uso: recuperar el corte abierto. Actor: cajero. Precondiciones: ninguna. Payload: ninguno. Respuesta: objeto con `status: "Abierto"`; 404 si no existe. Efectos DB: lectura. Siguiente: abrir ticket o abrir corte.

### POST /api/v1/pos/cash-expenses

Uso: registrar salida de caja. Actor: cajero/gerente. Precondiciones: corte abierto y permiso. Payload: `{"employee_id":1,"amount_cents":2500,"description":"Servilletas","category":"INSUMO","note":"Compra local"}`. Respuesta: `{"folio":"G000001","status":"Activo","amount_cents":2500}`. Errores: 400 importe, 403 permiso, 409 sin corte. Efectos DB: crea gasto y auditoría. Siguiente: resumen del corte.

### GET /api/v1/pos/cash-shifts/{cash_shift_id}/summary

Uso: calcular efectivo esperado, ventas, gastos y conteos. Actor: gerente. Precondiciones: corte existente. Payload: path `cash_shift_id`. Respuesta: `{"total_sales_cents":12000,"expected_cash_cents":109500,"paid_ticket_count":1}`. Errores: 404. Efectos DB: lecturas agregadas. Siguiente: cerrar corte.

### POST /api/v1/pos/cash-shifts/{cash_shift_id}/close

Uso: cerrar y congelar totales del corte. Actor: gerente. Precondiciones: corte abierto, sin tickets abiertos/en cobro; política de impresión satisfecha. Payload: `{"employee_id":1,"declared_cash_cents":109500,"note":"Cierre","allow_pending_print_jobs":true}`. Respuesta: `{"closed":true,"cash_shift":{"status":"Cerrado"},"print_job":{"job_type":"Corte","status":"Pendiente"}}`. Errores: 403, 404, 409. Efectos DB: actualiza corte, auditoría y trabajo de impresión. Siguiente: cola de impresión.

## POS: tickets, líneas y comandas

### POST /api/v1/pos/tables/{table_id}/open-ticket

Uso: abrir cuenta para una mesa. Actor: cajero. Precondiciones: corte abierto, mesa activa `Libre`, empleado activo. Payload: `{"employee_id":1,"waiter_employee_id":1,"guest_count":2,"note":"Ventana"}`. Respuesta: ticket con `status: "Abierto"`, `payment_status: "Sin pagar"`. Errores: 400 comensales, 404, 409 mesa/corte. Efectos DB: crea ticket, cambia mesa a `Ocupada`, registra transición y auditoría. Siguiente: agregar líneas.

### GET /api/v1/pos/tickets/{ticket_id}

Uso: recuperar encabezado y totales. Actor: cajero. Precondiciones: ticket existente. Payload: path. Respuesta: `{"id":1,"folio":"TK000001","status":"Abierto","total_cents":7000}`. Errores: 404. Efectos DB: lectura. Siguiente: listar/agregar líneas.

### GET /api/v1/pos/tickets/{ticket_id}/lines

Uso: listar detalle del ticket. Actor: cajero. Precondiciones: ticket existente. Payload: path. Respuesta: `[{"line_type":"Simple","status":"Capturado","quantity":1}]`. Errores: 404. Efectos DB: lectura. Siguiente: enviar ronda o agregar producto.

### POST /api/v1/pos/tickets/{ticket_id}/lines

Uso: agregar producto simple o paquete. Actor: cajero. Precondiciones: ticket `Abierto`, producto activo/visible y cantidad positiva. Payload: `{"product_id":1,"employee_id":1,"quantity":2,"note":"Sin cebolla"}`. Respuesta: `{"ticket":{...},"lines":[{"status":"Capturado"}]}`. Errores: 400 producto/cantidad, 404, 409 estado. Efectos DB: crea líneas/snapshots, recalcula totales y audita. Siguiente: enviar ronda.

### POST /api/v1/pos/tickets/{ticket_id}/send-round

Uso: enviar líneas `Capturado` a producción. Actor: cajero. Precondiciones: ticket abierto/en cobro y al menos una línea capturada. Payload: `{"employee_id":1}`. Respuesta: `{"command_batch":{"batch_type":"Pedido"},"station_orders":[{"status":"En cola"}],"print_jobs":[{"status":"Pendiente"}]}`. Errores: 404, 409 sin líneas/estado. Efectos DB: crea lote, órdenes y trabajos; cambia líneas a `Enviado a comanda` o `Impreso`; audita. Siguiente: listar órdenes o iniciar cobro.

### GET /api/v1/pos/tickets/{ticket_id}/station-orders

Uso: consultar órdenes lógicas por estación. Actor: cajero/cocina/barra. Precondiciones: ticket existente. Payload: path. Respuesta: `[{"folio":"CMD000001","status":"En cola","station_id":1}]`. Errores: 404. Efectos DB: lectura. Siguiente: monitoreo de producción (confirmación real aún pendiente).

### POST /api/v1/pos/ticket-lines/{line_id}/cancel

Uso: cancelar una línea y avisar a producción si ya fue enviada. Actor: gerente/cajero autorizado. Precondiciones: permiso, ticket no cobrado, motivo según UI. Payload: `{"employee_id":1,"reason":"Error de captura"}`. Respuesta: `{"line":{"status":"Cancelado"},"print_jobs_created":1}`. Errores: 403, 404, 409 línea/paquete/estado. Efectos DB: cancela línea(s), recalcula, crea cancelación de comanda y auditoría. Siguiente: consultar ticket.

### POST /api/v1/pos/tickets/{ticket_id}/cancel

Uso: cancelar la cuenta completa. Actor: gerente/cajero autorizado. Precondiciones: permiso y ticket no cobrado/cancelado. Payload: `{"employee_id":1,"reason":"Cliente se retiró"}`. Respuesta: `{"ticket":{"status":"Cancelado"},"lines_cancelled":2,"payments_cancelled":0,"table_released":true}`. Errores: 403, 404, 409. Efectos DB: cancela líneas/pagos, libera mesa, crea avisos y auditoría. Siguiente: cola de impresión o mesas.

## POS: cobro

### POST /api/v1/pos/tickets/{ticket_id}/start-payment

Uso: bloquear captura e iniciar cobro. Actor: cajero. Precondiciones: ticket `Abierto`, total positivo y ninguna línea `Capturado`. Payload: `{"employee_id":1}`. Respuesta: ticket con `status: "En cobro"`; mesa también `En cobro`. Errores: 404, 409. Efectos DB: cambia estados/fecha y audita. Siguiente: listar métodos y registrar pago.

### POST /api/v1/pos/tickets/{ticket_id}/payments

Uso: registrar abono o liquidación. Actor: cajero. Precondiciones: ticket `En cobro`, método activo; referencia cuando aplica. Payload: `{"employee_id":1,"payment_method_id":1,"amount_cents":7000,"received_cents":10000,"reference":null}`. Respuesta: `{"payment":{"status":"Activo","change_cents":3000},"ticket":{"status":"Cobrado","payment_status":"Pagado"},"closed":true}`. Errores: 400 importes/referencia, 404, 409. Efectos DB: crea pago; al liquidar consume inventario, libera mesa, imprime ticket y audita. Siguiente: listar pagos/print jobs.

### GET /api/v1/pos/tickets/{ticket_id}/payments

Uso: listar pagos y total activo. Actor: cajero/gerente. Precondiciones: ticket existente. Payload: path. Respuesta: `{"payments":[{"status":"Activo"}],"total_paid_cents":7000}`. Errores: 404. Efectos DB: lectura. Siguiente: completar pago o auditoría.

### GET /api/v1/pos/tickets/{ticket_id}/inventory-movements

Uso: rastrear consumo generado por venta. Actor: gerente. Precondiciones: ticket existente. Payload: path. Respuesta: `[{"movement_type":"Consumo venta","source_type":"Linea ticket"}]`. Errores: 404. Efectos DB: lectura. Siguiente: reporte de consumo.

### GET /api/v1/pos/print-jobs/pending

Uso: alias POS de trabajos pendientes. Actor: cajero. Precondiciones: ninguna. Payload: query opcional de impresora según schema. Respuesta: trabajos con `status: "Pendiente"`. Errores: 422 query. Efectos DB: lectura. Siguiente: flujo printing.

## Inventory

### GET /api/v1/inventory/items

Uso: listar insumos con existencia calculada. Actor: frontend administrativo. Precondiciones: catálogo. Payload: ninguno. Respuesta: `[{"sku":"INV-ARROZ","stock_status":"Sin stock","current_quantity":"0"}]`. Errores: 500. Efectos DB: agregación. Siguiente: stock individual o movimiento.

### GET /api/v1/inventory/items/{inventory_item_id}/stock

Uso: consultar stock de un insumo. Actor: gerente/almacén. Precondiciones: insumo existente. Payload: path. Respuesta: `{"stock_status":"Stock bajo","current_quantity":"500"}`. Errores: 404. Efectos DB: agregación. Siguiente: crear ajuste.

### POST /api/v1/inventory/movements

Uso: registrar ajuste/merma manual. Actor: gerente/almacén. Precondiciones: empleado con permiso e insumo activo. Payload: `{"inventory_item_id":1,"movement_type":"Ajuste entrada","quantity_base":"500","employee_id":1,"reason":"Conteo"}`. Respuesta: `{"movement_type":"Ajuste entrada","signed_quantity_base":"500"}`. Errores: 400 tipo/cantidad, 403, 404, 409. Efectos DB: movimiento, auditoría y actualización de alerta. Siguiente: consultar stock/alertas.

### POST /api/v1/inventory/purchase-receipts

Uso: procesar recepción y opcionalmente gasto pagado. Actor: gerente/almacén. Precondiciones: permisos, unidades convertibles, líneas válidas. Payload: `{"employee_id":1,"supplier_name":"Proveedor","amount_paid_cents":10000,"payment_method_id":1,"lines":[{"inventory_item_id":1,"quantity":"1","unit_id":2,"unit_cost_cents":10000}]}`. Respuesta: `{"status":"Procesada","lines":[{"status":"Procesada"}]}`. Errores: 400 conversión/datos, 403, 404, 409. Efectos DB: recepción, líneas, compras de inventario, posible gasto y auditoría. Siguiente: stock/alertas.

### GET /api/v1/inventory/stock-alerts/active

Uso: listar alertas abiertas. Actor: gerente/almacén. Precondiciones: ninguna. Payload: ninguno. Respuesta: `[{"alert_type":"Stock bajo","status":"Abierta"}]`. Errores: 500. Efectos DB: lectura. Siguiente: ajuste o recepción.

## Printing

### GET /api/v1/printing/jobs/pending

Uso: polling FIFO de pendientes. Actor: daemon impresión. Precondiciones: impresora lógica configurada. Payload: `?printer_key=COCINA&limit=50`. Respuesta: `[{"id":1,"job_type":"Comanda","status":"Pendiente"}]`. Errores: 422. Efectos DB: lectura. Siguiente: claim-next.

### POST /api/v1/printing/jobs/claim-next

Uso: tomar atómicamente el siguiente trabajo. Actor: daemon impresión. Precondiciones: trabajo pendiente y elegible. Payload: `{"worker_id":"daemon-cocina","printer_key":"COCINA"}`. Respuesta: trabajo `Tomado` o `null` si no hay. Errores: 409 carrera/estado. Efectos DB: cambia estado, incrementa intentos y fija toma. Siguiente: printed o failed.

### POST /api/v1/printing/jobs/{print_job_id}/printed

Uso: confirmar impresión lógica. Actor: daemon impresión. Precondiciones: trabajo `Tomado`. Payload: `{"worker_id":"daemon-cocina"}`. Respuesta: trabajo `Impreso`. Errores: 404, 409. Efectos DB: estado y fecha de impresión. Siguiente: claim-next.

### POST /api/v1/printing/jobs/{print_job_id}/failed

Uso: registrar fallo y backoff. Actor: daemon impresión. Precondiciones: trabajo `Tomado`. Payload: `{"worker_id":"daemon-cocina","error":"Sin papel","retry_delay_seconds":30}`. Respuesta: trabajo `Fallido` con `next_retry_at`. Errores: 404, 409. Efectos DB: estado/error/fechas. Siguiente: retry-failed.

### POST /api/v1/printing/jobs/retry-failed

Uso: reencolar fallidos vencidos. Actor: daemon impresión/gerente. Precondiciones: trabajos `Fallido` cuya espera terminó. Payload: `{"printer_key":"COCINA","limit":50}`. Respuesta: `{"retried":2,"jobs":[{"status":"Pendiente"}]}`. Errores: 422. Efectos DB: cambia a `Pendiente`, conserva último error. Siguiente: claim-next.

## Reports

Los cinco endpoints son de lectura, actor gerente/frontend administrativo, aceptan `date_from` y `date_to` ISO cuando aparecen y devuelven 400 para rango inválido.

### GET /api/v1/reports/operational-summary

Uso: tablero de ventas, tickets, impresión y alertas. Payload: `?date_from=2026-06-19`. Respuesta: `{"paid_ticket_count":4,"pending_print_jobs_count":1,"low_stock_alert_count":2}`. Efectos DB: agregaciones. Siguiente: desglose correspondiente.

### GET /api/v1/reports/sales-by-payment-method

Uso: ventas por método. Payload: rango opcional. Respuesta: `[{"method_key":"Efectivo","total_cents":120000,"payment_count":10}]`. Efectos DB: agregación. Siguiente: auditoría de corte.

### GET /api/v1/reports/sales-by-product

Uso: unidades e importe por producto cobrable. Payload: rango opcional. Respuesta: `[{"product_name":"Chela","quantity":12,"total_cents":84000}]`. Efectos DB: agregación. Siguiente: consumo de inventario.

### GET /api/v1/reports/inventory-consumption

Uso: consumo por insumo y tipo de movimiento. Payload: `?movement_type=Consumo%20venta`. Respuesta: `[{"inventory_item_name":"Sake","quantity_base":"1200"}]`. Efectos DB: agregación. Siguiente: inventario.

### GET /api/v1/reports/print-jobs-summary

Uso: medir cola/fallos por tipo y estado. Payload: rango opcional. Respuesta: `{"pending_count":1,"failed_count":2,"printed_count":20}`. Efectos DB: agregación. Siguiente: cola de impresión.

## Audit

### GET /api/v1/audit/events

Uso: buscar eventos paginados. Actor: gerente. Precondiciones: ninguna. Payload: `?event_type=Ticket%20cobrado&limit=50&offset=0`. Respuesta: `{"total":1,"items":[{"event_type":"Ticket cobrado","entity_type":"Ticket"}]}`. Errores: 400 paginación. Efectos DB: lectura. Siguiente: auditoría por ticket/corte.

### GET /api/v1/audit/tickets/{ticket_id}

Uso: reconstruir ciclo del ticket con pagos, líneas, impresión e inventario. Actor: gerente. Precondiciones: ticket existente. Payload: path. Respuesta: `{"ticket":{...},"events":[...],"payments":[...],"print_jobs":[...]}`. Errores: 404. Efectos DB: lectura. Siguiente: evento específico o reporte.

### GET /api/v1/audit/cash-shifts/{cash_shift_id}

Uso: reconstruir corte y contexto financiero. Actor: gerente. Precondiciones: corte existente. Payload: path. Respuesta: `{"cash_shift":{...},"events":[...],"expenses":[...],"payments":[...]}`. Errores: 404. Efectos DB: lectura. Siguiente: reporte por método.

## Preflight

### GET /api/v1/preflight/local-backend

Uso: validar configuración e invariantes antes de operar/sincronizar. Actor: frontend administrativo/soporte. Precondiciones: DB accesible. Payload: ninguno. Respuesta: `{"status":"OK","checks":[{"key":"database","status":"OK","message":"..."}],"summary":{...}}`; puede ser `WARNING` o `ERROR`. Errores: 500 sólo ante fallo no controlado. Efectos DB: lecturas. Siguiente: operar si `OK`, mostrar advertencias si `WARNING`, bloquear y corregir si `ERROR`.
