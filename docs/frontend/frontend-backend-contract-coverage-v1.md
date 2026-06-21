# Cobertura de contratos backend/frontend v1

## Fuente y alcance

Auditoría realizada el 20 de junio de 2026 contra `GET http://127.0.0.1:8000/openapi.json` y `frontend/src`. El contrato vivo contiene **71 rutas y 74 operaciones**. La tabla clasifica cada operación; «Sí (equivalente)» indica que la interfaz cubre la función mediante otra ruta oficial del mismo contrato.

Estados:

- **completo**: la operación tiene una interfaz funcional o una cobertura equivalente explícita.
- **parcial**: la interfaz consume la operación, pero no expone toda su capacidad de consulta.
- **pendiente**: no existe interfaz para esa operación.
- **no aplica**: operación de worker, diagnóstico o integración que no corresponde al operador.

## Matriz completa

| Dominio | Endpoint | ¿Existe frontend? | Estado | Pantalla o módulo | Notas |
| --- | --- | --- | --- | --- | --- |
| Seguridad | `POST /api/v1/auth/login-pin` | Sí | completo | Login | Inicio por PIN con respuesta contractual. |
| Seguridad | `GET /api/v1/auth/me` | Sí | completo | Sesión | Recupera empleado, roles y permisos. |
| Seguridad | `POST /api/v1/auth/logout` | Sí | completo | Sesión | Cierre explícito de sesión. |
| Seguridad | `GET /api/v1/operations/employees` | Sí | completo | `/security` | Lista de solo lectura sin datos sensibles. |
| Caja | `GET /api/v1/pos/cash-shifts/current` | Sí | completo | `/cash` | Resuelve la caja activa. |
| Caja | `POST /api/v1/pos/cash-shifts/open` | Sí | completo | `/cash` | Apertura confirmada por backend. |
| Caja | `GET /api/v1/pos/cash-shifts/{cash_shift_id}/summary` | Sí | completo | `/cash` | Resumen del turno activo. |
| Caja | `POST /api/v1/pos/cash-shifts/{cash_shift_id}/close` | Sí | completo | `/cash` | Cierre con captura contractual. |
| Caja | `POST /api/v1/pos/cash-expenses` | Sí | completo | `/cash` | Registro de gasto autorizado. |
| POS | `GET /api/v1/operations/tables` | Sí | completo | `/pos` | Mesas y estado operativo. |
| POS | `POST /api/v1/pos/tables/{table_id}/open-ticket` | Sí | completo | `/pos` | Abre o recupera cuenta de mesa. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}` | Sí | completo | `/pos` | Cuenta y totales confirmados. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}/lines` | Sí | completo | `/pos` | Productos de la cuenta. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/lines` | Sí | completo | `/pos` | Captura de producto. |
| POS | `POST /api/v1/pos/ticket-lines/{line_id}/modify` | Sí | completo | `/pos` | Modificación con motivo. |
| POS | `POST /api/v1/pos/ticket-lines/{line_id}/cancel` | Sí | completo | `/pos` | Cancelación de producto autorizada. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/cancel` | Sí | completo | `/pos` | Cancelación total con `TICKET_CANCEL`, motivo y confirmación del backend. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/send-round` | Sí | completo | `/pos` | Envío explícito de comanda. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}/station-orders` | Sí | completo | `/pos` | Estado de comandas por cuenta. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}/discounts` | Sí | completo | `/pos` | Descuentos existentes. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/discounts` | Sí | completo | `/pos` | Descuento o cortesía con permiso y motivo. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/start-payment` | Sí | completo | `/pos` | Inicia cobro con estado confirmado. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}/payments` | Sí | completo | `/pos` | Resumen y pagos de la cuenta. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/payments` | Sí | completo | `/pos` | Registra pago y usa cierre devuelto. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}/splits` | Sí | completo | `/pos` | Consulta las partes confirmadas de la cuenta. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/splits/equal` | Sí | completo | `/pos` | División entre 2 y 50 partes. |
| POS | `POST /api/v1/pos/tickets/{ticket_id}/splits/by-lines` | Sí | completo | `/pos` | División por productos completos sin cálculo local. |
| POS | `POST /api/v1/pos/ticket-splits/{split_id}/payments` | Sí | completo | `/pos` | Pago del importe contractual de cada parte. |
| POS | `GET /api/v1/pos/tickets/{ticket_id}/inventory-movements` | No | pendiente | Ninguno | Es historial por cuenta, no historial general de inventario. |
| Catálogo | `GET /api/v1/catalog/categories` | Sí | completo | `/pos` | Filtro de productos. |
| Catálogo | `GET /api/v1/catalog/products` | Sí | completo | `/pos` | Catálogo de venta. |
| Catálogo | `GET /api/v1/catalog/payment-methods` | Sí | completo | `/pos` | Formas de pago. |
| Catálogo | `GET /api/v1/catalog/stations` | Sí | completo | `/pos`, `/production` | Estaciones reales. |
| Catálogo | `GET /api/v1/catalog/variant-groups` | No | no aplica | Catálogo global | La venta usa la consulta específica por producto. |
| Catálogo | `GET /api/v1/catalog/products/{product_id}/variant-groups` | Sí | completo | `/pos` | Selector por grupo, cantidades y límites contractuales. |
| Producción | `GET /api/v1/production/station-orders` | Sí | completo | `/production` | Consulta por estación. |
| Producción | `POST /api/v1/production/station-orders/{station_order_id}/receive` | Sí | completo | `/production` | Acción Aceptar. |
| Producción | `POST /api/v1/production/station-orders/{station_order_id}/start` | Sí | completo | `/production` | Acción Iniciar. |
| Producción | `POST /api/v1/production/station-orders/{station_order_id}/complete` | Sí | completo | `/production` | Acción Terminar. |
| Producción | `POST /api/v1/production/station-orders/{station_order_id}/deliver` | Sí | completo | `/production` | Acción Entregar agregada en Fase 15. |
| Impresión | `GET /api/v1/printing/jobs/pending` | Sí | completo | `/printing` | Cola pendiente oficial. |
| Impresión | `GET /api/v1/pos/print-jobs/pending` | Sí (equivalente) | completo | `/printing` | La interfaz usa la ruta canónica de impresión. |
| Impresión | `GET /api/v1/printing/jobs/{print_job_id}` | Sí (equivalente) | parcial | `/printing` | La cola ya devuelve el detalle de cada pendiente; no hay búsqueda por identificador. |
| Impresión | `GET /api/v1/printing/printers` | No | pendiente | Ninguno | No existe panel de impresoras lógicas. |
| Impresión | `POST /api/v1/printing/jobs/retry-failed` | Sí | completo | `/printing` | Reintenta fallidos elegibles. |
| Impresión | `POST /api/v1/printing/jobs/{print_job_id}/reprint` | Sí | completo | `/printing` | Reimpresión con permiso y motivo. |
| Impresión | `POST /api/v1/printing/jobs/claim-next` | No | no aplica | Worker de impresión | Reservado al proceso que controla impresoras. |
| Impresión | `POST /api/v1/printing/jobs/{print_job_id}/printed` | No | no aplica | Worker de impresión | Confirmación física del worker. |
| Impresión | `POST /api/v1/printing/jobs/{print_job_id}/failed` | No | no aplica | Worker de impresión | Registro técnico del worker. |
| Inventario | `GET /api/v1/inventory/items` | Sí | completo | `/inventory` | Insumos y stock actual. |
| Inventario | `GET /api/v1/inventory/items/{inventory_item_id}/stock` | Sí (equivalente) | completo | `/inventory` | La lista contractual ya incluye `current_stock`. |
| Inventario | `GET /api/v1/inventory/stock-alerts/active` | Sí | completo | `/inventory` | Alertas activas. |
| Inventario | `POST /api/v1/inventory/movements` | Sí | completo | `/inventory` | Ajuste manual protegido por permiso. No existe `GET` en esta ruta. |
| Inventario | `POST /api/v1/inventory/purchase-receipts` | Sí | completo | `/inventory` | Recepción de una o más líneas; pago opcional según permisos reales. |
| Reportes | `GET /api/v1/reports/operational-summary` | Sí | completo | `/reports` | Resumen del día. |
| Reportes | `GET /api/v1/reports/sales-by-product` | Sí | completo | `/reports` | Ventas por producto. |
| Reportes | `GET /api/v1/reports/sales-by-payment-method` | Sí | completo | `/reports` | Panel de solo lectura agregado en Fase 15. |
| Reportes | `GET /api/v1/reports/inventory-consumption` | Sí | completo | `/reports` | Panel de solo lectura agregado en Fase 15. |
| Reportes | `GET /api/v1/reports/production-times` | Sí | completo | `/reports` | Tiempos por estación. |
| Reportes | `GET /api/v1/reports/print-jobs-summary` | Sí | completo | `/reports` | Resumen de impresión. |
| Auditoría | `GET /api/v1/audit/events` | Sí | parcial | `/audit` | Muestra 100 eventos; no hay paginación o filtros en UI. |
| Auditoría | `GET /api/v1/audit/tickets/{ticket_id}` | Sí | completo | `/audit` | Resumen detallado desde eventos vinculados a cuenta. |
| Auditoría | `GET /api/v1/audit/cash-shifts/{cash_shift_id}` | Sí | completo | `/audit` | Resumen detallado desde eventos vinculados a corte. |
| Sistema | `GET /health` | Sí | completo | `/`, `/system` | Salud del servicio local. |
| Sistema | `GET /api/v1/system/airtable-sync` | Sí | completo | `/`, `/system` | Estado y error operativo de sincronización. |
| Sistema | `POST /api/v1/system/airtable-sync/run` | Sí | completo | `/system` | Ejecución consolidada con confirmación para `ADMIN`. |
| Sistema | `POST /api/v1/system/airtable-sync/pull` | No | no aplica | Integración administrativa | La interfaz no expone direcciones separadas; usa `run`. |
| Sistema | `POST /api/v1/system/airtable-sync/push` | No | no aplica | Integración administrativa | La interfaz no expone direcciones separadas; usa `run`. |
| Sistema | `GET /api/v1/system/business-settings` | No | no aplica | Diagnóstico/configuración | No hay edición contractual y no es operación diaria. |
| Sistema | `GET /api/v1/system/db` | No | no aplica | Diagnóstico | Estado técnico no visible al operador. |
| Sistema | `GET /api/v1/system/seed-summary` | No | no aplica | Diagnóstico | Verificación técnica de datos base. |
| Sistema | `GET /api/v1/preflight/local-backend` | No | no aplica | Preflight local | Contrato de preparación técnica, no pantalla operativa. |
| Notificaciones | `GET /api/v1/notifications/sms` | No | no aplica | Integración de notificaciones | No forma parte del flujo POS solicitado. |
| Notificaciones | `POST /api/v1/notifications/sms/test` | No | no aplica | Diagnóstico de notificaciones | Acción de prueba técnica, no operador. |

## Huecos prioritarios revisados

| Pendiente conocido | Resultado contractual | Decisión |
| --- | --- | --- |
| Promociones | No existen rutas con `promotion` ni un contrato para aplicar promociones. | El panel permanece «En preparación». |
| Ventas por categoría | No existe endpoint de reporte por categoría. | El panel permanece «En preparación»; no se agrupa localmente. |
| Historial general de inventario | `/api/v1/inventory/movements` solo expone `POST`. | No se creó consulta ni historial falso. |
| Roles/permisos por empleado | Solo existe `GET /api/v1/operations/employees`, sin roles o permisos por empleado. | Se conserva lectura de empleados sin chips inventados. |
| Historial general de impresión | Solo existe listado de pendientes; el detalle requiere un identificador. | Se conserva la cola pendiente. |
| Entrega de comandas | Existe `POST .../{station_order_id}/deliver` con `employee_id`. | Se agregó la acción Entregar para estado `Terminada`. |

## Rutas y query keys frontend

- Las rutas activas de `navigationItems.ts` tienen componentes reales; ninguna cae en `ModulePlaceholder`.
- Los únicos placeholders visibles son Promociones y Ventas por categoría, ambos justificados por falta de contrato.
- Se eliminaron las claves reservadas sin consumo real: `discounts.promotions`, `inventory.movements`, `security.roles` y `security.permissions`.
- Se agregaron claves únicamente para los nuevos `GET` reales de ventas por forma de pago y consumo de inventario.

## Pendientes de interfaz con contrato

- `GET /api/v1/printing/printers` devuelve objetos sin propiedades definidas en OpenAPI; no se construyó una interfaz basada en campos no contractuales.
- `GET /api/v1/pos/tickets/{ticket_id}/inventory-movements` sigue siendo consulta por cuenta, no historial general; el detalle de auditoría muestra el conteo agregado contractual.
- No se ejecutó ninguna operación mutante durante esta auditoría.
