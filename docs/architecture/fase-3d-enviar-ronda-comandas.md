# Fase 3-D: enviar ronda y generar comandas lógicas

## Objetivo

Esta fase convierte las líneas `CAPTURED` de un ticket en una ronda inmutable de
producción. La operación crea comandas por estación y trabajos de impresión
lógicos, pero no se comunica con impresoras físicas.

## Endpoints

- `POST /api/v1/pos/tickets/{ticket_id}/send-round`: envía una nueva ronda.
- `GET /api/v1/pos/tickets/{ticket_id}/station-orders`: lista las comandas del
  ticket, incluyendo sus líneas.
- `GET /api/v1/pos/print-jobs/pending`: lista trabajos de impresión pendientes
  en orden FIFO.

## Servicios

- `app/services/order_service.py`: valida y envía rondas, resuelve estaciones y
  consulta comandas por ticket.
- `app/services/print_service.py`: resuelve impresoras activas y consulta la cola
  pendiente.

`send_round` hace `flush`, no `commit`. La ruta HTTP controla la transacción y
revierte todos los cambios ante un error de negocio.

## Reglas de envío

El ticket debe existir y estar en `OPEN` o `IN_PAYMENT`. El empleado debe existir
y estar activo. Solo se procesa una ronda cuando hay al menos una línea
`CAPTURED`; las líneas ya enviadas o canceladas quedan fuera.

El número de ronda es el máximo `round_number` registrado en `CommandBatch` para
el ticket más uno. Todas las líneas capturadas procesadas reciben ese número y
`sent_at`.

Las líneas `SIMPLE` y `PACKAGE_COMPONENT` se pueden enviar a producción. Primero
se usa `station_id_snapshot`; si está vacío se busca la asignación primaria
activa de `ProductStationAssignment`. Una línea sin estación queda `IMPRESO` y
no genera comanda ni trabajo. Una línea enviada a una estación queda
`ENVIADO_COMANDA`.

## Agrupación y registros generados

Cada ronda crea un `CommandBatch` de tipo `ORDER`. Las líneas producibles se
agrupan por estación y cada grupo crea:

1. Un `StationOrder` con folio de la secuencia `COMANDA` y estado `QUEUED`.
2. Un `StationOrderLine` por línea, con snapshots de producto y nota y acción
   `ADD`.
3. Un `PrintJob` con folio `IMPRESION`, estado `PENDING`, cero intentos y una
   clave de idempotencia por lote y comanda.

El texto de la comanda incluye `KANPAI`, `COMANDA`, folio del ticket, estación,
ronda, cantidades, productos y notas. Al final se registra un `AuditEvent`
`ROUND_SENT` asociado al ticket y al empleado.

Cada estación usa `ProductionStation.printer_key` para resolver una `Printer`
activa. El seed crea idempotentemente `CAJA`, `COCINA`, `BARRA_FRIA`,
`COCTELERIA` y `BARRA_CALIENTE`. Si falta la configuración o no hay una
impresora activa, la ronda completa falla con conflicto HTTP 409.

## Combos

`PACKAGE_PARENT` representa el cargo comercial y no se manda a producción. Se
marca `IMPRESO` dentro de la ronda para no volver a procesarlo. Sus líneas
`PACKAGE_COMPONENT` sí se agrupan y envían según su estación propia.

## Impresión física

Los `PrintJob` son una cola persistente y auditable. Esta fase no abre puertos,
drivers ni conexiones de red; por tanto, no puede marcar trabajos como impresos.
Un daemon posterior consumirá la cola, controlará reintentos y actualizará el
resultado físico.

## QA

```powershell
uv run pytest
uv run ruff check .
git diff --check
```

## Prueba con curl

Con Uvicorn disponible en el puerto 8011 y un ticket abierto con líneas
capturadas:

```powershell
curl.exe -X POST http://127.0.0.1:8011/api/v1/pos/tickets/1/send-round `
  -H "Content-Type: application/json" `
  -d '{"employee_id":1}'

curl.exe http://127.0.0.1:8011/api/v1/pos/tickets/1/station-orders
curl.exe http://127.0.0.1:8011/api/v1/pos/print-jobs/pending
```

## Pendiente

- Iniciar cobro.
- Registrar pagos.
- Cerrar tickets.
- Descontar inventario.
- Implementar el daemon de impresión física.
