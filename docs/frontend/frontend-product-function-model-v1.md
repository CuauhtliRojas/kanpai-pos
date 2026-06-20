# Modelo Funcional Frontend V1 — Kanpai POS

## 1. Propósito

Este documento define el comportamiento funcional esperado del frontend de Kanpai POS. El frontend es una aplicación de escritorio Tauri que consume exclusivamente el Backend V1 local mediante FastAPI.

El frontend no contiene reglas de negocio propias. Su función es presentar estados, capturar intención del operador, llamar endpoints locales y reflejar respuestas del backend.

## 2. Principios funcionales

El frontend debe cumplir estas reglas:

- No calcula totales si el backend ya los devuelve.
- No modifica SQLite directamente.
- No llama Airtable directamente.
- No guarda tokens Airtable.
- No inventa permisos.
- No decide si una acción está permitida si el backend debe decidirlo.
- No oculta errores operativos.
- No permite flujos ambiguos en caja, tickets, pagos, cancelaciones o impresión.
- No mezcla administración con operación rápida.

## 3. Módulos funcionales

### 3.1 Acceso y sesión

Objetivo: identificar al empleado activo mediante PIN.

Funciones:

- Login por código de empleado y PIN.
- Guardar `session_token` localmente en frontend.
- Consultar sesión actual.
- Cerrar sesión.
- Mostrar cajero activo en topbar.
- Usar `employee_id` de la sesión para acciones operativas.

Endpoints base:

```text
POST /api/v1/auth/login-pin
GET /api/v1/auth/me
POST /api/v1/auth/logout
```

La sesión frontend debe ser simple. Foundation V1 puede usar almacenamiento local, pero en fases posteriores debe evaluarse si Tauri debe guardar token con mecanismo más seguro.

### 3.2 Topbar operativo

Objetivo: mostrar solo información crítica.

Contenido:

- Cajero activo.
- Mesa actual.
- Estado de sync.
- Estado backend si hay error.
- Menú hamburguesa.

El topbar no debe contener navegación completa ni filtros.

### 3.3 Caja y cortes

Objetivo: controlar el inicio y cierre de operación diaria.

Funciones:

- Consultar corte actual.
- Abrir corte con fondo inicial.
- Ver resumen de corte.
- Registrar gasto de caja.
- Cerrar corte con efectivo declarado.
- Mostrar diferencias de caja.
- Mostrar pendientes de impresión antes de cierre.

Endpoints base:

```text
GET /api/v1/pos/cash-shifts/current
POST /api/v1/pos/cash-shifts/open
GET /api/v1/pos/cash-shifts/{cash_shift_id}/summary
POST /api/v1/pos/cash-shifts/{cash_shift_id}/close
POST /api/v1/pos/cash-expenses
```

Regla UX: si no hay corte abierto, el POS debe bloquear venta y dirigir a apertura de corte.

### 3.4 Mesas

Objetivo: seleccionar mesa y abrir ticket operativo.

Funciones:

- Listar mesas.
- Mostrar estados de mesas.
- Seleccionar mesa actual.
- Abrir ticket para mesa.
- Entrar al ticket activo de mesa.

Endpoints base:

```text
GET /api/v1/operations/tables
POST /api/v1/pos/tables/{table_id}/open-ticket
GET /api/v1/pos/tickets/{ticket_id}
```

Regla UX: el POS siempre debe mostrar qué mesa está activa. Agregar producto sin mesa/ticket activo debe estar bloqueado.

### 3.5 Productos y catálogo POS

Objetivo: seleccionar productos vendibles de forma rápida.

Funciones:

- Listar categorías.
- Listar productos visibles en POS.
- Consultar grupos de variantes.
- Mostrar productos por categoría.
- Agregar producto al ticket.
- Agregar nota o variantes si aplica.

Endpoints base:

```text
GET /api/v1/catalog/categories
GET /api/v1/catalog/products
GET /api/v1/catalog/variant-groups
GET /api/v1/catalog/products/{product_id}/variant-groups
POST /api/v1/pos/tickets/{ticket_id}/lines
```

Regla UX: productos deben ser botones grandes. El frontend no debe permitir cantidades no enteras en POS.

### 3.6 Ticket y líneas

Objetivo: mostrar el ticket activo y permitir acciones sobre líneas.

Funciones:

- Consultar ticket.
- Consultar líneas.
- Agregar producto.
- Modificar nota de línea.
- Cancelar línea con motivo.
- Mostrar subtotal, descuentos, impuestos y total devueltos por backend.

Endpoints base:

```text
GET /api/v1/pos/tickets/{ticket_id}
GET /api/v1/pos/tickets/{ticket_id}/lines
POST /api/v1/pos/tickets/{ticket_id}/lines
POST /api/v1/pos/ticket-lines/{line_id}/modify
POST /api/v1/pos/ticket-lines/{line_id}/cancel
POST /api/v1/pos/tickets/{ticket_id}/cancel
```

Regla UX: cancelaciones deben requerir confirmación y motivo si el backend lo requiere o lo permite.

### 3.7 Rondas y comandas

Objetivo: enviar líneas capturadas a estaciones de producción.

Funciones:

- Enviar ronda.
- Consultar comandas/station orders del ticket.
- Mostrar si existen líneas pendientes de enviar.
- Mostrar trabajos de impresión generados.

Endpoints base:

```text
POST /api/v1/pos/tickets/{ticket_id}/send-round
GET /api/v1/pos/tickets/{ticket_id}/station-orders
```

Regla UX: el botón “ENVIAR RONDA” debe ser grande y visible cuando existan líneas capturadas pendientes.

### 3.8 Cobro y pagos

Objetivo: iniciar cobro, registrar pagos y cerrar ticket si el backend lo determina.

Funciones:

- Iniciar cobro.
- Consultar pagos del ticket.
- Registrar pago.
- Mostrar pagado, restante y cambio.
- Detectar cierre del ticket según respuesta backend.
- Soportar pago parcial.
- Soportar distintos métodos de pago.

Endpoints base:

```text
POST /api/v1/pos/tickets/{ticket_id}/start-payment
GET /api/v1/pos/tickets/{ticket_id}/payments
POST /api/v1/pos/tickets/{ticket_id}/payments
GET /api/v1/catalog/payment-methods
```

Regla UX: el frontend no decide si el ticket cerró. Usa el campo `closed` o el estado del ticket devuelto por backend.

### 3.9 Cuentas divididas

Objetivo: permitir división de cuenta por partes o por líneas.

Funciones:

- Consultar splits.
- Dividir por partes iguales.
- Dividir por líneas.
- Pagar split.

Endpoints base:

```text
GET /api/v1/pos/tickets/{ticket_id}/splits
POST /api/v1/pos/tickets/{ticket_id}/splits/equal
POST /api/v1/pos/tickets/{ticket_id}/splits/by-lines
POST /api/v1/pos/ticket-splits/{split_id}/payments
```

Regla UX: esta función debe estar fuera del flujo principal inicial para no estorbar a operaciones simples.

### 3.10 Producción

Objetivo: consultar y avanzar comandas por estación.

Funciones:

- Listar órdenes de estación.
- Filtrar por estación.
- Recibir comanda.
- Iniciar preparación.
- Completar preparación.
- Marcar entrega.

Endpoints base:

```text
GET /api/v1/production/station-orders
POST /api/v1/production/station-orders/{station_order_id}/receive
POST /api/v1/production/station-orders/{station_order_id}/start
POST /api/v1/production/station-orders/{station_order_id}/complete
POST /api/v1/production/station-orders/{station_order_id}/deliver
```

Regla UX: aunque el proyecto prioriza comandas físicas, esta pantalla puede funcionar como vista administrativa o respaldo operativo.

### 3.11 Impresión

Objetivo: supervisar la cola lógica de impresión y permitir reintentos.

Funciones:

- Listar impresoras.
- Listar trabajos pendientes.
- Ver detalle de trabajo.
- Reintentar fallidos.
- Reimprimir trabajo con motivo.
- Marcar impreso/fallido solo desde worker o pantalla autorizada si aplica.

Endpoints base:

```text
GET /api/v1/printing/printers
GET /api/v1/printing/jobs/pending
GET /api/v1/printing/jobs/{print_job_id}
POST /api/v1/printing/jobs/retry-failed
POST /api/v1/printing/jobs/{print_job_id}/reprint
POST /api/v1/printing/jobs/claim-next
POST /api/v1/printing/jobs/{print_job_id}/printed
POST /api/v1/printing/jobs/{print_job_id}/failed
```

Regla UX: POS no debe depender visualmente de impresión exitosa para permitir flujo si backend ya permite continuidad.

### 3.12 Inventario

Objetivo: consulta y operación mínima de inventario.

Funciones:

- Listar insumos.
- Consultar stock.
- Ver alertas activas.
- Crear movimiento manual.
- Registrar recepción de compra.

Endpoints base:

```text
GET /api/v1/inventory/items
GET /api/v1/inventory/items/{inventory_item_id}/stock
GET /api/v1/inventory/stock-alerts/active
POST /api/v1/inventory/movements
POST /api/v1/inventory/purchase-receipts
```

Regla UX: inventario no pertenece al flujo principal del POS; debe vivir en administración/hamburguesa.

### 3.13 Reportes y auditoría

Objetivo: consulta gerencial y trazabilidad.

Funciones:

- Resumen operativo.
- Ventas por producto.
- Ventas por método de pago.
- Consumo de inventario.
- Tiempos de producción.
- Resumen de impresión.
- Auditoría por ticket.
- Auditoría por corte.
- Eventos de auditoría.

Endpoints base:

```text
GET /api/v1/reports/operational-summary
GET /api/v1/reports/sales-by-product
GET /api/v1/reports/sales-by-payment-method
GET /api/v1/reports/inventory-consumption
GET /api/v1/reports/production-times
GET /api/v1/reports/print-jobs-summary
GET /api/v1/audit/tickets/{ticket_id}
GET /api/v1/audit/cash-shifts/{cash_shift_id}
GET /api/v1/audit/events
```

Regla UX: reportes no deben aparecer en navegación principal visible del POS.

### 3.14 Sistema y sincronización

Objetivo: consultar salud local y administrar sync manual solo con confirmaciones.

Funciones:

- Health backend.
- Estado DB.
- Seed summary.
- Business settings.
- Estado scheduler Airtable.
- Pull manual.
- Push manual.
- Run manual.

Endpoints base:

```text
GET /health
GET /api/v1/system/db
GET /api/v1/system/seed-summary
GET /api/v1/system/business-settings
GET /api/v1/system/airtable-sync
POST /api/v1/system/airtable-sync/pull
POST /api/v1/system/airtable-sync/push
POST /api/v1/system/airtable-sync/run
```

Regla UX: acciones manuales de sync deben vivir en administración y requerir confirmación explícita.
