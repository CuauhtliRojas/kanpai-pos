# Fase 3-J: cola de impresión operativa

## Objetivo

Esta fase convierte `PrintJob` en una cola operativa local. Un daemon futuro
puede consultar trabajos, reclamarlos, reportar éxito o fallo y reactivar
fallos sin reconstruir tickets, comandas o cortes. No se envían bytes a una
impresora y no se implementa ESC/POS todavía.

## Endpoints

Todos los endpoints nuevos viven bajo `/api/v1/printing`:

- `GET /jobs/pending?printer_key=BARRA_FRIA&limit=100`: lista trabajos
  `PENDING` en orden FIFO.
- `POST /jobs/claim-next`: reclama el siguiente trabajo disponible para
  `printer_key` y `worker_id`; responde `{"job": null}` si no existe uno.
- `POST /jobs/{print_job_id}/printed`: marca como `PRINTED` un trabajo
  reclamado por el mismo worker.
- `POST /jobs/{print_job_id}/failed`: guarda el error, marca `FAILED` y agenda
  retry a 60 segundos.
- `POST /jobs/retry-failed`: reactiva fallos vencidos. `reset_all=true`
  reactiva inmediatamente todos los seleccionados.

El endpoint previo `GET /api/v1/pos/print-jobs/pending` permanece como alias
compatible y delega en el mismo servicio de consulta.

Los errores esperados usan `400` para campos vacíos, `404` para impresora o
trabajo inexistente y `409` para estado u ownership incompatibles. No se
devuelven trazas internas.

## Servicios

`app/services/print_queue_service.py` contiene las operaciones FIFO, claim,
printed, failed y retry. Todas hacen `flush` cuando mutan datos y ninguna hace
`commit`; el límite transaccional está en las rutas.

`app/services/print_service.py` conserva la resolución de impresoras activas y
la generación de snapshots. También expone `sanitize_print_content`, usada por
los nuevos trabajos `COMANDA`, `TICKET`, `CORTE` y `CANCELACION_COMANDA`.

Los permisos de empleado siguen aplicándose en los flujos POS que originan
operaciones mediante `permission_service.py`. Los endpoints del daemon no
reciben `employee_id` en su contrato y validan ownership con `worker_id`; por
eso esta fase no inventa una autorización de empleado para el proceso local.

## Ciclo de vida de PrintJob

Estados conceptuales y persistidos:

- `PENDING`: disponible para claim cuando `next_retry_at` es nulo o venció.
- `CLAIMED`: reservado por `claimed_by` desde `claimed_at`.
- `PRINTED`: completado; registra `printed_at` y limpia `last_error`.
- `FAILED`: registra `failed_at`, `last_error` y `next_retry_at`.
- `CANCELLED`: estado reservado para cancelación futura; esta fase no ofrece
  una transición hacia él.

No hay enum ni nombres históricos alternativos: los estados se guardan con
estas cadenas. Los snapshots históricos no se modifican.

### Claim

El claim valida una `Printer` activa y ejecuta un `UPDATE` condicional con una
subconsulta FIFO y `RETURNING`. Estado, ownership, timestamp e incremento de
`attempts` se escriben en una sola sentencia. Así dos transacciones no pueden
tomar el mismo id. SQLite serializa escrituras y esto es suficiente para un
solo POS local. Un escenario con múltiples procesos de alta concurrencia debe
migrar a una base con locking de filas o endurecer esta estrategia.

### Printed, failed y retry

`printed` y `failed` exigen estado `CLAIMED`. Si `claimed_by` tiene valor debe
coincidir con el worker que reporta. Un fallo conserva su mensaje y queda
programado para retry 60 segundos después.

El retry normal solo toma fallos con `next_retry_at <= now`. Puede filtrarse
por impresora. El reset manual ignora la fecha y limpia `next_retry_at` para
que el trabajo reencolado esté disponible inmediatamente. `last_error` se
conserva como diagnóstico.

## Sanitización ASCII

`sanitize_print_content(content)`:

- normaliza acentos (`Estación` a `Estacion`);
- intenta reparar tokens con mojibake UTF-8 común de Windows;
- normaliza CRLF y CR a `\n`;
- conserva saltos de línea;
- elimina emojis, tabuladores, NUL y controles no imprimibles;
- garantiza un resultado ASCII para una térmica básica.

Solo se sanitizan snapshots al crear trabajos nuevos. No se reescriben filas
históricas.

## Esquema y tablas tocadas

La migración `e4a91bc6d2f0` agrega a `print_jobs`:

- `claimed_at DATETIME NULL`
- `claimed_by VARCHAR(160) NULL`
- `failed_at DATETIME NULL`
- `next_retry_at DATETIME NULL`

`last_error` y `printed_at` ya existían. No se modifica otra tabla. `printers`
solo se consulta para validar clave y estado activo.

## Compatibilidad con el daemon futuro

El daemon hará polling por impresora, reclamará un snapshot inmutable, lo
convertirá al protocolo físico y reportará `printed` o `failed`. La cola no
depende del fabricante, conexión USB/red ni formato ESC/POS. Esta separación
evita mezclar transacciones de venta con I/O físico lento o no confiable.

## QA

```powershell
$env:DEBUG = "false"
uv run alembic upgrade head
uv run pytest
uv run ruff check .
git diff --check
```

Prueba manual con Uvicorn en `127.0.0.1:8011`:

```powershell
$base = "http://127.0.0.1:8011/api/v1/printing"

Invoke-RestMethod "$base/jobs/pending?printer_key=BARRA_FRIA&limit=20"

$claim = @{ printer_key = "BARRA_FRIA"; worker_id = "local-daemon-01" } |
  ConvertTo-Json
Invoke-RestMethod "$base/jobs/claim-next" -Method Post `
  -ContentType "application/json" -Body $claim

$printed = @{ worker_id = "local-daemon-01" } | ConvertTo-Json
Invoke-RestMethod "$base/jobs/1/printed" -Method Post `
  -ContentType "application/json" -Body $printed

$failed = @{
  worker_id = "local-daemon-01"
  error_message = "Impresora sin papel"
} | ConvertTo-Json
Invoke-RestMethod "$base/jobs/1/failed" -Method Post `
  -ContentType "application/json" -Body $failed

$retry = @{ printer_key = "BARRA_FRIA"; reset_all = $true } | ConvertTo-Json
Invoke-RestMethod "$base/jobs/retry-failed" -Method Post `
  -ContentType "application/json" -Body $retry
```

## Pendientes

- daemon físico ESC/POS;
- reportes operativos;
- hardening pre-sync;
- sincronización con Airtable.
