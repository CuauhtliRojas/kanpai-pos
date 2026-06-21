# Flujos avanzados de cuenta frontend v1

## Variantes

Al elegir un producto, el POS consulta `GET /api/v1/catalog/products/{product_id}/variant-groups`. Sin grupos activos agrega como antes. Con grupos activos muestra las opciones reales, sus cambios de precio y controles de cantidad respetando `min_select` y `max_select`. El alta envía `variant_selections` a `POST /api/v1/pos/tickets/{ticket_id}/lines`; no calcula el total final.

## Cuenta dividida

La sección Cuenta permite:

- consultar `GET /api/v1/pos/tickets/{ticket_id}/splits`;
- dividir entre 2 y 50 partes con `POST .../splits/equal`;
- crear partes por productos completos con `POST .../splits/by-lines`;
- pagar una parte abierta mediante `POST /api/v1/pos/ticket-splits/{split_id}/payments`.

Las partes y sus importes siempre provienen del backend. Cuando existen divisiones activas, el pago directo de la cuenta se oculta. La mesa se libera solo cuando el pago de una parte devuelve `ticket_closed: true`.

## Cancelación total

La acción se muestra únicamente con `TICKET_CANCEL` y para cuentas no cobradas ni canceladas. Exige motivo y usa `POST /api/v1/pos/tickets/{ticket_id}/cancel`. La UI solo informa cancelación y libera su contexto cuando la respuesta confirma `table_released`.

## Validación de esta fase

No se creó ninguna división, pago o cancelación real. La validación fue estática mediante TypeScript y build de producción.
