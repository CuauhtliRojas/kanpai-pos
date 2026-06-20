# Fase 3-L: hardening pre-sync

## Objetivo

Cerrar el backend local-first con diagnóstico reproducible, validación de
invariantes, limpieza segura de datos QA y documentación operativa. Esta fase
no agrega dependencias, integración con Airtable, sincronización, frontend ni
impresión física.

## Endpoint creado

`GET /api/v1/preflight/local-backend` devuelve `status`, `database`, `checks` y
`summary`. El estado general es `ERROR` si falla un check crítico, `WARNING` si
solo existen condiciones operativas que requieren atención y `OK` en estado
sano.

El resumen incluye cortes abiertos, tickets abiertos, tickets en cobro,
impresiones pendientes o fallidas y alertas activas de stock.

## Checks preflight

- conexión SQLite y consulta de tablas críticas: `cash_shifts`, `tickets`,
  `ticket_lines`, `payments`, `print_jobs`, `inventory_movements` y
  `audit_events`;
- empleado admin activo con rol `ADMIN`;
- métodos `CASH`, `CARD` y `TRANSFER`;
- mesas activas, secuencias de folio, impresoras lógicas, productos e insumos
  demo;
- máximo un corte abierto;
- máximo un ticket activo (`OPEN` o `IN_PAYMENT`) por mesa;
- tickets `PAID` con recetas ya consumidos en inventario;
- ausencia de pagos `ACTIVE` en tickets cancelados;
- snapshot de impresora no vacío en todos los `PrintJob`;
- `source_type` presente en movimientos `SALE_CONSUMPTION`.

Trabajos de impresión fallidos y alertas de stock activas generan `WARNING`, no
`ERROR`. Ningún check modifica datos.

## Scripts creados

### Invariantes pre-sync

```powershell
uv run python scripts/check_pre_sync_invariants.py
```

Ejecuta exactamente el mismo servicio que el endpoint, imprime checks y
resumen, y termina con código `1` solo ante errores críticos. Advertencias y
estado sano terminan con código `0`.

### Reset QA

```powershell
uv run python scripts/reset_operational_data.py --yes
```

El reset requiere confirmación explícita, se ejecuta en una transacción, es
idempotente y elimina únicamente stock alerts, movimientos/recepciones,
gastos, cola lógica de impresión, comandas, auditoría, eventos de mesa,
detalles de ticket, pagos, tickets y cortes. Después deja todas las mesas en
`FREE`.

Sin `--yes` muestra una advertencia y no abre una transacción de borrado. No
elimina productos, categorías, estaciones, impresoras, métodos de pago,
empleados, seguridad, unidades, insumos, recetas ni folios.

### Smoke local

Requiere Uvicorn activo en `127.0.0.1:8011`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/smoke_local_backend.ps1
```

Valida health, pytest, ruff, diff, seed y el flujo corte → ticket → producto →
ronda → cobro → pago. Después consulta consumo, impresión, reportes, auditoría
y preflight. Termina con `SMOKE OK`. No borra datos ni hace commit de Git; si
ya existe un corte abierto o no hay mesa libre, falla sin intentar limpiar el
entorno. Pytest usa una SQLite temporal migrada y sembrada, por lo que sus
fixtures de limpieza no afectan la base operativa atendida por Uvicorn.

## QA directo

```powershell
uv run pytest
uv run ruff check .
git diff --check
uv run python scripts/check_pre_sync_invariants.py
Invoke-RestMethod http://127.0.0.1:8011/api/v1/preflight/local-backend
```

## Criterios para pasar a Airtable/sync

- migraciones aplicadas y seed idempotente;
- suite, lint y diff check sin errores;
- script de invariantes sin errores críticos;
- flujo smoke completo confirmado en una base QA controlada;
- preflight `OK`, o `WARNING` entendido y aceptado;
- reset QA probado y respaldos operativos definidos antes de usarlo.

Cumplidos estos puntos puede iniciar la auditoría del Airtable actual. Todavía
no corresponde diseñar tablas remotas ni implementar pull, push o resolución
de conflictos.
