# Cobertura del procedimiento operativo

## Cierre Fase 3-M

Los pendientes de producción quedan cubiertos en backend: aceptación, inicio, terminado y entrega; actores y timestamps; promedios por estación; modificación explícita; descuentos, porcentajes y cortesías autorizadas; política IVA central; y reimpresión auditada. La tabla histórica inferior conserva la fotografía previa a 3-M.

Continúan fuera de alcance el frontend, Airtable/sincronización y la impresión física ESC/POS. La cola sólo produce snapshots lógicos.

`Procedimiento operativo.txt` no se encontró dentro de `kanpai-pos` ni en su directorio padre durante esta auditoría. La matriz usa como fuente conceptual los requisitos operativos enumerados en el encargo y el comportamiento comprobable de routers/modelos actuales. Debe reconciliarse con el archivo original cuando esté disponible.

| Requisito operativo | Soportado | Endpoint/modelo relacionado | Observaciones | Pendiente técnico |
|---|---|---|---|---|
| Recepción de clientes | Parcial | `GET /operations/tables`, `DiningTable` | Permite ver disponibilidad y comensales al abrir cuenta. | No existe registro separado de recepción ni hora de llegada. |
| Apertura de cuenta | Sí | `POST /pos/tables/{id}/open-ticket`, `Ticket` | Valida corte, mesa y empleado; ocupa mesa. | — |
| Toma de pedidos | Sí | `POST /pos/tickets/{id}/lines`, `TicketLine` | Productos simples, paquetes, notas y snapshots. | — |
| Separación cocina/barra | Sí | `send-round`, `ProductionStation`, `StationOrder` | Agrupa por estación y crea impresión lógica. | — |
| Confirmación producción | Parcial | `StationOrder.status`, fechas de estación | Se crea `En cola`, pero no hay endpoints de aceptación/inicio/terminado/entrega. | Confirmación real de cocina/barra. |
| Hora recepción/inicio/terminado | Parcial | `received_at`, `started_at`, `finished_at` | Columnas existen, flujo no las actualiza. | Endpoints y actor de estación. |
| Modificaciones | Parcial | agregar/cancelar línea | Se modela como nueva captura o cancelación. | Evento/acción explícita `Modificacion`. |
| Cancelaciones | Sí | cancel line/ticket, `AuditEvent`, `PrintJob` | Permiso, motivo, aviso lógico y auditoría. | — |
| Entrega producto | No | `StationOrder.delivered_at` | Campo sin endpoint ni transición. | Confirmación de entrega. |
| Impresión cuenta | Parcial | trabajo tipo `Ticket`, cola printing | Se genera snapshot y ciclo lógico. | Impresión física fuera de alcance. |
| Cierre cuenta | Sí | start-payment/payments, `Payment`, `Ticket` | Pagos parciales, cambio, cierre, inventario y liberación. | — |
| Ventas por día | Sí | `/reports/operational-summary` y filtros fecha | Totales y conteos. | Afinar zona horaria/cortes según necesidad fiscal. |
| Ventas por categoría | No | categoría snapshot disponible | No existe endpoint agregado por categoría. | Reporte dedicado. |
| Ventas por producto | Sí | `/reports/sales-by-product` | Excluye componentes no cobrables. | — |
| Operación: tickets | Sí | operational summary, ticket audit | Estados abiertos/en cobro/cobrados/cancelados. | — |
| Operación: tiempos | No | timestamps parciales | No se calculan tiempos promedio cocina/barra/servicio. | Definir hitos y reportes SLA. |
| Descuentos | Parcial | `TicketDiscount` | Modelo existe, sin servicio/endpoints. | Promociones/descuentos y autorización. |
| Cortesías | No | sin flujo | No hay tipo ni autorización específica. | Modelo, permisos, API y reporte. |
| Auditoría de cancelaciones | Sí | `/audit/*`, eventos en español | Motivo, actor y snapshots. | — |
| Auditoría de cortes | Sí | audit cash shift, eventos/summary | Apertura, cierre, gastos y pagos relacionados. | — |
| Reimpresiones | Parcial | permiso `REPRINT`, cola | No existe operación explícita que genere y audite una reimpresión. | Endpoint y evento de reimpresión. |

## Pendientes explícitos pre-Airtable

- Confirmación real de producción cocina/barra y transiciones autorizadas.
- Captura efectiva de hora de recepción, inicio, terminado y entrega.
- Tiempos promedio de cocina, barra y servicio.
- Promociones, descuentos y cortesías de extremo a extremo.
- Reimpresión explícitamente auditada.
- Modificación explícita tipo `Modificacion` en lugar de inferirla por cancelación + alta.
