# POS: cuenta, pagos y cierre (Fase 8)

## Alcance

La Fase 8 permite revisar la cuenta activa, iniciar cobro, registrar uno o varios pagos y liberar la mesa cuando el servicio confirma el cierre.

## Cuenta e inicio de cobro

- La cuenta muestra productos, subtotal y total devueltos por el servicio.
- Cobrar requiere una mesa, cuenta activa, productos y ninguna línea pendiente de enviar.
- Iniciar cobro cambia la cuenta al estado de pago mediante el contrato existente.

## Pagos y cierre

- Los métodos disponibles provienen del catálogo activo.
- Los montos escritos en pesos se convierten a centavos sin usar valores decimales para el envío.
- Efectivo permite capturar recibido. El cambio mostrado proviene del pago registrado.
- Tarjeta y transferencia solicitan referencia porque el catálogo lo indica.
- Un pago mixto se registra como varios pagos parciales con métodos reales.
- No existe una operación separada para cerrar la cuenta. El pago que cubre el restante devuelve `closed`; solo entonces se limpia la operación actual y se muestra que la mesa fue liberada.
- El cierre genera procesos internos del servicio, pero esta interfaz no afirma que exista impresión física.

## Contratos consumidos

- `GET /api/v1/pos/tickets/{ticket_id}`
- `GET /api/v1/pos/tickets/{ticket_id}/lines`
- `POST /api/v1/pos/tickets/{ticket_id}/start-payment`
- `GET /api/v1/pos/tickets/{ticket_id}/payments`
- `POST /api/v1/pos/tickets/{ticket_id}/payments`
- `GET /api/v1/catalog/payment-methods`

## QA esperado

1. Abrir una cuenta de prueba, agregar productos y enviar la comanda.
2. Confirmar que Cobrar muestra subtotal y total correctos.
3. Iniciar cobro y registrar un pago parcial.
4. Verificar Pagado y Restante con valores devueltos por el servicio.
5. Completar el restante con el mismo método u otro método real.
6. Confirmar que la cuenta se cierra, la mesa queda libre y la selección actual se limpia.
7. Confirmar que no se afirma impresión física.
