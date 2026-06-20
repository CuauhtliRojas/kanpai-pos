# Manual operativo de sincronización Airtable/SQLite

## Arquitectura y alcance

SQLite/FastAPI es la fuente operativa local-first. Airtable sirve como backoffice de catálogo, configuración y administración, y como espejo gerencial de la operación. No existe sincronización bidireccional libre: cada tabla tiene una dirección definida y todos los flujos son upsert sin deletes.

Fuera de alcance en v1:

- Comandas operativas estructuradas, incluidos lotes y órdenes de estación.
- Kardex detallado de movimientos de inventario.

## Uso del backoffice Airtable

Se pueden editar en Airtable productos, precios, `activo`, `visible_pos`, insumos, recetas, categorías, mesas, estaciones, impresoras lógicas, métodos de pago y canales. Las tablas de operación que reciben cortes, tickets, líneas, pagos, impresión, SMS y auditoría son espejos de solo lectura.

En las vistas de trabajo se deben ocultar:

- Campos técnicos: `id_sqlite`, `estado_sync`, `revision_remota`, `actualizado_sqlite_en`, `actualizado_airtable_en`, `ultimo_pull_en`, `ultimo_push_en` y `error_sync`.
- Backlinks automáticos generados por Airtable.
- Tablas técnicas, por ejemplo `_AirtableSchemaMigrations`.

Eliminar un registro en Airtable no lo elimina de SQLite. Para retirar un elemento del POS se usa `activo=false` o `visible_pos=false`. Un borrado real requiere una migración o script controlado; los sincronizadores no exponen operaciones delete.

## Sincronización manual

Los scripts siguen disponibles y exigen confirmación literal para escribir:

```powershell
uv run python airtable/scripts/pull_airtable_to_sqlite.py --dry-run
uv run python airtable/scripts/pull_airtable_to_sqlite.py --execute --confirm PULL_AIRTABLE_TO_SQLITE

uv run python airtable/scripts/push_sqlite_to_airtable.py --dry-run
uv run python airtable/scripts/push_sqlite_to_airtable.py --execute --confirm PUSH_SQLITE_TO_AIRTABLE
```

El pull manual conserva su preflight completo de drift y seed. El push replica únicamente operación local hacia Airtable.

## Sincronización automática

La tarea existe solo mientras el proceso FastAPI/Uvicorn está activo. No corre por request ni por venta. El valor recomendado es 60 minutos; se permite bajar a 30 minutos cuando el plan y volumen de llamadas lo soporten. Valores menores a 30 son rechazados por configuración.

Configuración:

```env
AIRTABLE_SYNC_ENABLED=false
AIRTABLE_SYNC_INTERVAL_MINUTES=60
AIRTABLE_SYNC_PULL_ENABLED=true
AIRTABLE_SYNC_PUSH_ENABLED=true
AIRTABLE_SYNC_RUN_ON_STARTUP=false
AIRTABLE_SYNC_SKIP_PULL_DURING_ACTIVE_SHIFT=true
```

Con `AIRTABLE_SYNC_RUN_ON_STARTUP=false`, el primer ciclo ocurre al cumplirse el intervalo. Con `true`, se lanza un ciclo al iniciar y luego se respeta el intervalo. Si faltan `AIRTABLE_API_TOKEN` o `AIRTABLE_BASE_ID`, la API arranca normalmente y registra un warning; el scheduler no inicia.

Cada ciclo ejecuta pull y luego push según sus flags. Un lock impide ciclos solapados dentro del proceso. El cliente limita las solicitudes a 5 por segundo por base, procesa lotes de hasta 10 y reintenta `429`, errores transitorios `5xx` y fallos de red con backoff. No hay deletes.

Cuando `AIRTABLE_SYNC_SKIP_PULL_DURING_ACTIVE_SHIFT=true`, se omite el pull si SQLite tiene un corte abierto o tickets `Abierto`/`En cobro`. Así no cambian catálogo, precios o configuración a mitad de servicio. El push sí se ejecuta porque Airtable solo recibe el espejo operativo.

Solo una instancia de Uvicorn debe tener `AIRTABLE_SYNC_ENABLED=true`. Con múltiples workers o réplicas, habilitarlo en una sola instancia para evitar schedulers independientes.

Estado de solo lectura:

```text
GET /api/v1/system/airtable-sync
```

Expone configuración efectiva, ciclo en curso, timestamps, último estado y último error. Los reportes detallados continúan en `airtable/reports/`.

## Actualización desde Excel

1. Actualizar `airtable/imports/Kanpai.xlsx`.
2. Perfilar el archivo:
   `uv run python airtable/scripts/profile_excel_seed.py`.
3. Ejecutar seed dry-run:
   `uv run python airtable/scripts/seed_airtable_from_excel.py --dry-run`.
4. Ejecutar el seed con la confirmación indicada por el script.
5. Ejecutar pull dry-run.
6. Ejecutar pull con `--execute --confirm PULL_AIRTABLE_TO_SQLITE`.
7. Ejecutar `uv run python scripts/check_pre_sync_invariants.py`.

No habilitar la sincronización automática para sustituir la revisión del perfil o de un seed con cambios masivos.

## QA end-to-end

### Airtable a SQLite

1. Hacer un cambio seguro y reversible en un catálogo Airtable.
2. Ejecutar pull dry-run y revisar reporte.
3. Ejecutar pull real.
4. Verificar el valor en SQLite y en la API correspondiente.

### API/operación local a Airtable

1. Registrar una venta local mediante la API o el POS.
2. Ejecutar push dry-run y revisar creates/updates.
3. Ejecutar push real.
4. Repetir push dry-run y exigir `creates=0`, `updates=0`, sin warnings ni errores.

La adaptación y validación del frontend se hará en una fase separada; no forma parte de este cierre.

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
