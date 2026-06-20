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

| Airtable | Create | Update | Unchanged | Skipped | Error |
| --- | ---: | ---: | ---: | ---: | ---: |
| CortesCaja | 1 | 0 | 0 | 0 | 0 |
| Tickets | 1 | 0 | 0 | 0 | 0 |
| LineasTicket | 1 | 0 | 0 | 0 | 0 |
| Pagos | 1 | 0 | 0 | 0 | 0 |
| TrabajosImpresion | 3 | 0 | 0 | 0 | 0 |
| HistorialSMS | 4 | 0 | 0 | 0 | 0 |
| EventosAuditoria | 24 | 0 | 0 | 0 | 0 |

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
