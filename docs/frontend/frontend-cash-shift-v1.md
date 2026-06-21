# Caja operativa inicial

## Alcance de Fase 4

La ruta `/cash` consulta el corte abierto, permite abrir caja con fondo inicial, muestra el resumen calculado por el servidor, registra gastos y presenta un cierre explícito con efectivo contado.

No incluye POS, mesas, productos, tickets, comandas, cobro ni reportes.

## Operaciones consumidas

- `GET /api/v1/pos/cash-shifts/current`
- `POST /api/v1/pos/cash-shifts/open`
- `GET /api/v1/pos/cash-shifts/{cash_shift_id}/summary`
- `POST /api/v1/pos/cash-shifts/{cash_shift_id}/close`
- `POST /api/v1/pos/cash-expenses`

## Permisos

- `CASH_SHIFT_OPEN`: abrir caja.
- `CASH_SHIFT_CLOSE`: cerrar caja.
- `EXPENSE_CREATE`: registrar gasto.

El empleado se toma de la sesión activa; no se captura manualmente.

## Flujo con caja cerrada

La consulta sin corte abierto se interpreta como caja cerrada. El operador captura el fondo inicial en pesos y confirma la apertura. El importe se convierte a centavos antes de enviarse.

## Flujo con caja abierta

Se muestran folio, hora de apertura, fondo inicial y el resumen entregado por el servidor. El gasto solicita motivo y monto. El cierre solicita efectivo contado y requiere una segunda acción visible antes de ejecutarse.

## Importes

Los campos aceptan pesos con hasta dos decimales. Por ejemplo, `150.50` se convierte a `15050` centavos mediante operaciones enteras. Los totales mostrados provienen del resumen del servidor; el frontend no los recalcula.

## Pendiente para fases posteriores

No se implementan ventas, administración de tickets, impresión operativa, notas de cierre ni manejo manual de trabajos de impresión pendientes.

## QA esperado

1. Iniciar sesión y abrir Caja desde el menú.
2. Confirmar que se distingue entre caja cerrada y abierta.
3. Validar rechazo de importes vacíos, negativos o con más de dos decimales.
4. Abrir caja solo en un entorno donde sea seguro crear un corte real.
5. Con caja abierta, confirmar que el resumen carga y que los gastos respetan permisos.
6. Comprobar que el cierre exige efectivo contado; no confirmarlo durante QA si el corte contiene operación real.
7. Confirmar que los mensajes al operador no muestran términos internos.
