# Ajustes de pedido frontend v1

## Contratos verificados

La implementación se basó en el OpenAPI vivo consultado el 20 de junio de 2026. Las únicas operaciones específicas disponibles son:

- `POST /api/v1/pos/ticket-lines/{line_id}/modify`
- `POST /api/v1/pos/ticket-lines/{line_id}/cancel`

No existen rutas de autorización por PIN o supervisor. Tampoco existe una operación que cree un ticket nuevo para una modificación.

## Modificaciones

Desde la cuenta activa, cada producto ajustable tiene una acción compacta para capturar una nota obligatoria. La interfaz solo confirma el resultado después de una respuesta correcta.

El contrato real:

- actualiza la nota de la línea;
- crea un registro de modificación y auditoría con el empleado activo;
- si la línea ya fue enviada y tiene una orden de estación, crea un trabajo de impresión de tipo modificación;
- si la línea sigue capturada, conserva el cambio como pendiente de enviar;
- no crea otro ticket ni otra orden de estación.

Después de guardar se actualizan la cuenta, sus productos, las comandas consultadas y la cola de impresión.

## Cancelaciones autorizadas

La cancelación exige un motivo en la interfaz y usa el empleado de la sesión. El servicio valida directamente el permiso existente `TICKET_CANCEL`; no se implementó autorización local ni solicitud de PIN.

No se ofrece cancelación cuando:

- la cuenta no está abierta o en cobro;
- el producto ya está cancelado;
- el producto es un componente de paquete que debe cancelarse desde su paquete padre.

El servicio impide cancelar productos de cuentas cobradas o canceladas, registra producto, motivo, empleado y hora, recalcula totales y crea avisos de cancelación para productos ya enviados cuando corresponde.

Después de cancelar se actualizan cuenta, productos, comandas, mesas y cola de impresión.

## Estado de la fase

- Modificaciones: soportadas con el contrato real, sin creación de ticket nuevo.
- Cancelaciones autorizadas: soportadas mediante `TICKET_CANCEL` y sesión actual.
- Promociones y descuentos: pendientes.
- No se modificó ni canceló ninguna línea real durante la implementación.
