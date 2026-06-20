# Fase 3-M: cierre del procedimiento operativo

## Alcance

Esta fase completa el backend local de producción, descuentos, impuestos, modificaciones y reimpresión. No conecta Airtable, no agrega frontend y no envía bytes ESC/POS.

## Producción cocina/barra

Cada `StationOrder` nace `En cola` al enviar una ronda y sólo admite:

`En cola` → `Recibida` → `En preparacion` → `Terminada` → `Entregada`.

`Cancelada` es terminal. Cada transición registra fecha, empleado actor y `AuditEvent`. Entregada significa que el mesero recogió y entregó el producto.

Endpoints:

- `GET /api/v1/production/station-orders`
- `POST /api/v1/production/station-orders/{id}/receive`
- `POST /api/v1/production/station-orders/{id}/start`
- `POST /api/v1/production/station-orders/{id}/complete`
- `POST /api/v1/production/station-orders/{id}/deliver`

## Tiempos

`GET /api/v1/reports/production-times` agrupa por estación. Recepción es `received_at-created_at`, preparación es `completed_at-started_at` y servicio total es `delivered_at-created_at`. Cada promedio usa sólo órdenes con el par de timestamps requerido.

## Modificación explícita

`POST /api/v1/pos/ticket-lines/{line_id}/modify` conserva la nota vigente, agrega `TicketLineNote`, crea `TicketLineModification` y audita. Si la línea ya fue enviada y tiene orden de estación, encola un snapshot ASCII tipo `Modificacion`; si sigue capturada no imprime.

## Descuentos, promociones y cortesías

`POST /api/v1/pos/tickets/{ticket_id}/discounts` exige ticket `Abierto`, empleado activo y `DISCOUNT_AUTHORIZE`. Soporta `Monto`, `Porcentaje` y `Cortesia`; nunca permite un acumulado superior al subtotal. `GET` en la misma ruta lista los registros. Se recalculan descuento, impuesto y total y se audita `Descuento aplicado` o `Cortesia aplicada`.

## Política fiscal

`configuracion_negocio` persiste `impuestos_activos`, `tasa_impuesto_bps`, `impuesto_incluido` y `etiqueta_impuesto`. El seed usa IVA 16 %, no incluido. La base gravable es subtotal menos descuentos. Si el impuesto está incluido, `tax_cents` informa el componente y `total_cents` no se incrementa.

`GET /api/v1/system/business-settings` expone la política. No hay PATCH porque todavía no existe un permiso administrativo fiscal explícito.

## Reimpresión auditada

`GET /api/v1/printing/jobs/{id}` inspecciona el snapshot. `POST /api/v1/printing/jobs/{id}/reprint` exige `REPRINT` y motivo, conserva documento, impresora y relaciones, genera una clave idempotente nueva, deja estado `Pendiente` y registra `Reimpresion solicitada`. El reporte de impresión incluye `reprint_count`.

## Persistencia y migración

La revisión Alembic `b3f4c8d91a20` agrega actores de producción, política fiscal, metadatos de descuento y `modificaciones_linea_ticket`. Los atributos Python permanecen en inglés y el contrato físico SQLite en español. El reset QA elimina las nuevas transacciones y conserva catálogos y seed.

## Fuera de alcance

- frontend;
- Airtable y sincronización;
- impresión física ESC/POS.
