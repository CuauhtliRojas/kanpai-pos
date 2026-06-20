# Runbook SQLite -> Airtable operational push v1

## Contrato operativo

SQLite es la fuente operativa local-first. Airtable funciona como espejo administrativo y de lectura gerencial; no sustituye a SQLite ni recibe autoridad para operar el POS. El flujo es un upsert idempotente y nunca borra registros Airtable.

El push v1 incluye, en orden de dependencia:

1. CortesCaja.
2. Tickets.
3. LineasTicket.
4. Pagos.
5. TrabajosImpresion.
6. HistorialSMS.
7. EventosAuditoria.

Quedan fuera de alcance v1 por decisión arquitectónica:

- Comandas operativas estructuradas: lotes, órdenes de estación y líneas permanecen locales porque forman parte del ciclo operativo de producción.
- MovimientosInventario detallados: el kardex unitario permanece local; Airtable recibe supervisión gerencial de ventas y consumo, no cada movimiento.

Estas exclusiones no son bloqueos del push v1 y no autorizan agregar tablas o modificar el schema Airtable.

## Ejecución controlada

Checklist previo:

- `check_airtable_drift.py` termina sin warnings ni errores.
- `check_pre_sync_invariants.py` termina en `PRE-SYNC PREFLIGHT: OK`.
- Existe un backup local de `data/kanpai_pos.db` bajo `data/backups/`.
- El dry-run termina con `Warnings: 0` y `Errores: 0`.
- Los conteos y links planeados corresponden a la operación que se desea reflejar.

Dry-run:

```powershell
uv run python airtable/scripts/push_sqlite_to_airtable.py --dry-run
```

Execute deliberado:

```powershell
uv run python airtable/scripts/push_sqlite_to_airtable.py --execute --confirm PUSH_SQLITE_TO_AIRTABLE
```

La confirmación literal es obligatoria. Un dry-run exitoso no autoriza por sí mismo el execute.

## Primer execute real

El primer execute operativo real terminó sin warnings ni errores y creó:

| Airtable          | Create | Update | Unchanged | Skipped | Error |
| ----------------- | -----: | -----: | --------: | ------: | ----: |
| CortesCaja        |      1 |      0 |         0 |       0 |     0 |
| Tickets           |      1 |      0 |         0 |       0 |     0 |
| LineasTicket      |      1 |      0 |         0 |       0 |     0 |
| Pagos             |      1 |      0 |         0 |       0 |     0 |
| TrabajosImpresion |      3 |      0 |         0 |       0 |     0 |
| HistorialSMS      |      4 |      0 |         0 |       0 |     0 |
| EventosAuditoria  |     24 |      0 |         0 |       0 |     0 |

Resultado global: `Warnings: 0`, `Errores: 0`.

Después del execute, drift permaneció en 513 checks OK, preflight terminó OK y no quedaron cortes ni tickets abiertos. Había tres trabajos de impresión pendientes y cero alertas de stock activas.

## Checklist posterior

- Repetir el dry-run y exigir idempotencia: `creates=0`, `updates=0` y los registros previamente enviados como `unchanged`.
- Confirmar `Warnings: 0` y `Errores: 0`.
- Repetir drift y exigir cero warnings/errores.
- Repetir preflight y exigir estado OK.
- Conservar el reporte runtime para diagnóstico local; los reportes generados están ignorados por git.

Si el dry-run posterior propone updates, revisar primero normalización de fechas, links, números, booleanos y valores vacíos. No ejecutar nuevamente hasta explicar cada diferencia.

## Reglas permanentes

- No borrar registros Airtable desde este flujo.
- No fabricar operación en Airtable.
- No modificar schema durante un push.
- SQLite conserva la autoridad operativa; Airtable es un espejo administrativo.

## Ejecución programada

El push también puede ejecutarse desde el scheduler de FastAPI mientras Uvicorn está activo. Se recomienda un intervalo de 60 minutos y nunca menos de 30. No se dispara por request ni por venta. La tarea reutiliza este mismo upsert, aplica throttling de 5 requests/segundo y backoff ante `429`/errores transitorios.

La omisión preventiva del pull durante un corte o ticket activo no bloquea el push operativo. Configuración, operación, endpoint de estado y restricciones para múltiples workers se documentan en [airtable_sync_operating_manual.md](airtable_sync_operating_manual.md).

El último push operativo validado quedó idempotente: `creates=0`, `updates=0`, `unchanged=35`, `warnings=0`, `errores=0`.

## Sincronización manual por endpoint local

Además del scheduler ligado al proceso Uvicorn/FastAPI, el backend expone endpoints locales para disparar sincronización sin esperar el intervalo configurado.

### Endpoints disponibles

- `GET /api/v1/system/airtable-sync`: consulta el estado del scheduler.
- `POST /api/v1/system/airtable-sync/pull`: ejecuta sincronización Airtable -> SQLite.
- `POST /api/v1/system/airtable-sync/push`: ejecuta sincronización SQLite -> Airtable.
- `POST /api/v1/system/airtable-sync/run`: ejecuta ciclo completo Airtable -> SQLite y SQLite -> Airtable.

### Payload seguro por defecto

Por defecto, los endpoints manuales deben ejecutarse como `dry_run`. Esto permite validar el plan de sincronización sin escribir cambios.

```json
{
  "dry_run": true
}
```

### Ejecución real con confirmación explícita

Para ejecutar cambios reales se requiere confirmación explícita según la dirección de sincronización.

Airtable -> SQLite:

```json
{
  "dry_run": false,
  "confirm": "PULL_AIRTABLE_TO_SQLITE"
}
```

SQLite -> Airtable:

```json
{
  "dry_run": false,
  "confirm": "PUSH_SQLITE_TO_AIRTABLE"
}
```

Ciclo completo pull + push:

```json
{
  "dry_run": false,
  "confirm": "RUN_AIRTABLE_SYNC_NOW"
}
```

### Reglas operativas

La sincronización no se ejecuta por cada request del frontend. El POS sigue siendo local-first: SQLite es la fuente operativa y Airtable funciona como catálogo, configuración, administración y espejo gerencial.

La política de sincronización es upsert sin deletes. Borrar registros manualmente en Airtable no borra registros en SQLite. Para retirar elementos del POS se debe usar `activo=false` o `visible_pos=false`, según aplique. Los borrados reales deben hacerse mediante migración o script controlado.

El pull puede omitirse si hay corte abierto, tickets abiertos o tickets en cobro, salvo que se mande `force_pull_during_active_shift=true`. Esta regla evita cambiar catálogo, precios o configuración durante una operación activa.

El push puede correr durante operación porque solo replica desde SQLite hacia Airtable el espejo administrativo: cortes, tickets, líneas, pagos, trabajos de impresión, historial SMS y auditoría.

### Frecuencia recomendada

El scheduler automático corre mientras Uvicorn/FastAPI está activo, si `AIRTABLE_SYNC_ENABLED=true`.

Configuración recomendada:

```env
AIRTABLE_SYNC_ENABLED=true
AIRTABLE_SYNC_INTERVAL_MINUTES=60
AIRTABLE_SYNC_PULL_ENABLED=true
AIRTABLE_SYNC_PUSH_ENABLED=true
AIRTABLE_SYNC_RUN_ON_STARTUP=false
AIRTABLE_SYNC_SKIP_PULL_DURING_ACTIVE_SHIFT=true
```

El intervalo mínimo permitido es de 30 minutos. No se recomienda sincronizar por cada venta ni por cada consulta del frontend, porque eso volvería al POS dependiente de Airtable/internet y aumentaría el riesgo de límites de API.

### QA mínimo del endpoint manual

Validar estado:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/system/airtable-sync" | ConvertTo-Json -Depth 20
```

Validar pull sin escribir:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/system/airtable-sync/pull" `
  -Method POST `
  -Body (@{ dry_run = $true } | ConvertTo-Json) `
  -ContentType "application/json" |
  ConvertTo-Json -Depth 30
```

Validar push sin escribir:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/system/airtable-sync/push" `
  -Method POST `
  -Body (@{ dry_run = $true } | ConvertTo-Json) `
  -ContentType "application/json" |
  ConvertTo-Json -Depth 30
```

Ejecución real de pull:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/system/airtable-sync/pull" `
  -Method POST `
  -Body (@{ dry_run = $false; confirm = "PULL_AIRTABLE_TO_SQLITE" } | ConvertTo-Json) `
  -ContentType "application/json" |
  ConvertTo-Json -Depth 30
```

Ejecución real de push:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/system/airtable-sync/push" `
  -Method POST `
  -Body (@{ dry_run = $false; confirm = "PUSH_SQLITE_TO_AIRTABLE" } | ConvertTo-Json) `
  -ContentType "application/json" |
  ConvertTo-Json -Depth 30
```

Después de cualquier ejecución real deben quedar limpias estas validaciones:

```powershell
uv run python airtable/scripts/check_airtable_drift.py
uv run python airtable/scripts/pull_airtable_to_sqlite.py --dry-run
uv run python airtable/scripts/push_sqlite_to_airtable.py --dry-run
uv run python scripts/check_pre_sync_invariants.py
```
