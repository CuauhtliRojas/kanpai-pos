# Kanpai POS - Fase 3-C: agregar productos al ticket

## Objetivo

Esta fase permite consultar el catálogo capturable y agregar productos simples o
paquetes a un ticket abierto. Las líneas conservan snapshots de catálogo y el
ticket actualiza sus totales dentro de la misma transacción.

Los productos `DEV-CHELA`, `DEV-SAKE` y `DEV-CHELA-SAKE` son datos temporales de
desarrollo. El seed es idempotente y no representa el menú real.

## Endpoints

- `GET /api/v1/catalog/products`: lista productos activos y visibles en POS.
- `GET /api/v1/pos/tickets/{ticket_id}/lines`: lista líneas por orden de creación.
- `POST /api/v1/pos/tickets/{ticket_id}/lines`: agrega un producto y devuelve las
  líneas creadas junto con los totales resultantes.

La API responde `400` para datos de negocio inválidos, `404` para entidades que
no existen y `409` cuando el estado del ticket impide capturar. No expone trazas.

## Servicios creados o modificados

- `product_service.list_pos_products`: consulta el catálogo capturable.
- `product_service.get_ticket_lines`: consulta las líneas de un ticket existente.
- `product_service.add_product_to_ticket`: valida, crea líneas, recalcula totales
  y registra auditoría; hace `flush`, pero no `commit`.
- `seed.seed_development_products`: crea productos, componentes y asignaciones de
  estación de desarrollo sin duplicarlos.

## Producto simple

Solo se captura si el ticket está `OPEN`, el empleado existe y está activo, y el
producto existe, está activo, visible y tiene precio positivo. La cantidad debe
ser un entero positivo.

Se crea una línea `SIMPLE` con precio `NORMAL`, estado `CAPTURED`, nota, empleado
creador y snapshots de nombre, SKU, categoría y estación primaria. La auditoría
usa el evento `TICKET_LINE_ADDED`.

## Combo o paquete

Un producto `PACKAGE` requiere configuración y componentes activos. Se crea una
línea cobrable `PACKAGE_PARENT` con precio `PACKAGE_PRICE`; después se crean sus
líneas `PACKAGE_COMPONENT`, vinculadas al padre, con precio cero y modo
`INCLUDED_IN_PACKAGE`.

Cada componente usa `station_id_override` cuando está configurado; de lo
contrario usa su asignación primaria activa. Sin asignación, el snapshot queda
en `null`. La auditoría usa `PACKAGE_LINE_ADDED`.

## Tablas tocadas

| Tabla | Uso |
| --- | --- |
| `products`, `menu_categories` | Catálogo, precios y snapshots |
| `product_station_assignments`, `production_stations` | Estación primaria |
| `product_packages`, `product_package_items` | Configuración y componentes |
| `employees`, `tickets` | Validaciones de captura |
| `ticket_lines` | Líneas simples, padres y componentes |
| `ticket_discounts` | Total vigente de descuentos |
| `audit_events` | Eventos de línea o paquete agregado |

## Reglas de totales

El subtotal suma únicamente líneas no canceladas de tipo `SIMPLE` y
`PACKAGE_PARENT`. Las líneas `PACKAGE_COMPONENT` nunca incrementan el importe.
`discount_cents` se recalcula desde los descuentos registrados; `tax_cents`
conserva el impuesto vigente porque esta fase no introduce cálculo fiscal. El
total es `max(subtotal - descuento + impuesto, 0)`.

## Pendiente

- Enviar ronda y crear comandas por estación.
- Impresión real de comanda.
- Movimientos y consumo de inventario.
- Inicio de cobro.
- Pago, cierre del ticket y liberación de mesa.
