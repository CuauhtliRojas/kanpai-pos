# Mapa del contrato SQLite en español

Regla: tablas y columnas usan `snake_case` sin espacios. Los valores funcionales son español legible y sí admiten espacios. Atributos Python y claves JSON permanecen en inglés para conservar el contrato HTTP.

## Valores normativos

| Dominio | Anterior | Persistido oficial |
|---|---|---|
| Ticket | `OPEN` / `IN_PAYMENT` / `PAID` / `CANCELLED` | `Abierto` / `En cobro` / `Cobrado` / `Cancelado` |
| Pago de ticket | `UNPAID` / `PAID` / `CANCELLED` | `Sin pagar` / `Pagado` / `Cancelado` |
| Línea | `CAPTURED` / `ENVIADO_COMANDA` / `IMPRESO` / `CANCELLED` | `Capturado` / `Enviado a comanda` / `Impreso` / `Cancelado` |
| Tipo línea | `SIMPLE` / `PACKAGE_PARENT` / `PACKAGE_COMPONENT` | `Simple` / `Paquete padre` / `Componente de paquete` |
| Precio | `NORMAL` | `Normal` |
| Comanda | `ORDER` / `QUEUED` / `ADD` | `Pedido` / `En cola` / `Agregar` |
| Tipo impresión | `COMANDA` / `TICKET` / `CORTE` / `CANCELACION_COMANDA` | `Comanda` / `Ticket` / `Corte` / `Cancelacion comanda` |
| Estado impresión | `PENDING` / `CLAIMED` / `PRINTED` / `FAILED` / `CANCELLED` | `Pendiente` / `Tomado` / `Impreso` / `Fallido` / `Cancelado` |
| Corte | `OPEN` / `CLOSED` | `Abierto` / `Cerrado` |
| Pago/gasto | `ACTIVE` / `CANCELLED` | `Activo` / `Cancelado` |
| Método | `CASH` / `CARD` / `TRANSFER` | `Efectivo` / `Tarjeta` / `Transferencia` |
| Movimiento | `PURCHASE` / `ADJUSTMENT_IN` / `ADJUSTMENT_OUT` / `WASTE` / `SALE_CONSUMPTION` | `Compra` / `Ajuste entrada` / `Ajuste salida` / `Merma` / `Consumo venta` |
| Stock | `OK` / `LOW_STOCK` / `OUT_OF_STOCK` | `Correcto` / `Stock bajo` / `Sin stock` |
| Alerta | `LOW_STOCK` / `OPEN` / `RESOLVED` | `Stock bajo` / `Abierta` / `Resuelta` |
| Recepción | `PROCESSED` | `Procesada` |

Valores adicionales detectados y traducidos: mesa `FREE` → `Libre`; producto `PACKAGE` → `Paquete`; recepción `DRAFT/PENDING` → `Borrador/Pendiente`; sync `ACTIVE/PENDING/IDLE` → `Activo/Pendiente/Inactivo`; familias `MASS/VOLUME/COUNT` → `Masa/Volumen/Conteo`; conexión `LOGICAL/USB` → `Logica/USB`; autorización `APPROVED` → `Aprobada`.

## Auditoría

`event_type` se persiste en español legible: por ejemplo `TICKET_OPENED` → `Ticket abierto`, `ROUND_SENT` → `Ronda enviada`, `PAYMENT_CREATED` → `Pago creado` y `PURCHASE_RECEIPT_PROCESSED` → `Recepcion procesada`. `entity_type`, claves de permisos, folios, SKU, claves de estación y claves de secuencia permanecen como identificadores técnicos; no son estados presentados al usuario.

## Nombres físicos

Todas las tablas pasan a español (`tickets` → `tickets`, `ticket_lines` → `lineas_ticket`, `cash_shifts` → `cortes_caja`, `station_orders` → `ordenes_estacion`, `print_jobs` → `trabajos_impresion`, `inventory_movements` → `movimientos_inventario`, etc.). `tickets` se conserva porque ya es español de uso operativo.

Todas las columnas se traducen mediante un mapa central del ORM: `status` → `estado`, `payment_status` → `estado_pago`, `created_at` → `fecha_creacion`, `updated_at` → `fecha_actualizacion`, `ticket_id` → `ticket_id`, `line_type` → `tipo_linea`, `job_type` → `tipo_trabajo`, `movement_type` → `tipo_movimiento`, `status_cache` → `estado_temporal` y `sync_status` → `estado_sincronizacion`. Los nombres acabados en `_id` conservan ese sufijo y nunca contienen espacios.

## Compatibilidad HTTP

Métodos y rutas no cambian. Las claves JSON siguen en inglés (`status`, `payment_status`, `movement_type`); sus valores son los oficiales de esta tabla. No se aceptan claves técnicas antiguas en endpoints que reciben tipos o estados.
