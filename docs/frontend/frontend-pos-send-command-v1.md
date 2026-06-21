# POS: envío de comanda (Fase 7)

## Alcance

La Fase 7 agrega una confirmación explícita para enviar los productos capturados de la cuenta activa. Agregar un producto sigue sin enviar la comanda.

## Confirmar pedido

- El envío requiere cuenta activa, empleado autenticado y al menos una línea con estado `Capturado`.
- La interfaz solicita confirmación antes de ejecutar el envío.
- Un resultado correcto actualiza la cuenta, sus líneas, las mesas y las comandas asociadas.
- La interfaz solo muestra “Comanda enviada” después de una respuesta correcta.
- El envío genera trabajos lógicos según la respuesta del servicio; la interfaz no afirma que exista impresión física.

## Comandas por estación

- Las comandas se consultan por cuenta y se agrupan mediante el identificador de estación devuelto.
- Los nombres se obtienen del catálogo de estaciones; no se clasifican productos localmente como Cocina o Barra.
- Cada grupo muestra folio, estado devuelto, producto y cantidad.
- Esta fase no permite recibir, iniciar, terminar ni entregar producción.

## Contratos consumidos

- `POST /api/v1/pos/tickets/{ticket_id}/send-round`
- `GET /api/v1/pos/tickets/{ticket_id}`
- `GET /api/v1/pos/tickets/{ticket_id}/lines`
- `GET /api/v1/pos/tickets/{ticket_id}/station-orders`
- `GET /api/v1/catalog/stations`

## QA esperado

1. Abrir una cuenta de prueba y agregar productos.
2. Confirmar que las líneas capturadas aparecen pendientes de enviar.
3. Presionar “Enviar comanda” y confirmar la acción.
4. Verificar que el éxito solo aparece después de una respuesta correcta.
5. Confirmar que las líneas actualizadas ya no aparecen pendientes.
6. Verificar las comandas agrupadas con los nombres reales de estación.
7. Confirmar que no se muestra impresión física ni acciones de producción.
