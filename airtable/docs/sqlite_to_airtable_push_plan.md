# Plan SQLite -> Airtable para operación POS

## Contrato

SQLite continúa como única fuente operativa local-first. Airtable recibe una copia de supervisión y backoffice; este flujo no lee cambios operativos de regreso a SQLite, no borra registros remotos y no modifica el schema Airtable. El comando es dry-run por defecto. La escritura requiere simultáneamente `--execute --confirm PUSH_SQLITE_TO_AIRTABLE`.

Cada espejo usa `id_sqlite` como llave idempotente. El folio se conserva como dato de negocio y diagnóstico, no como identidad primaria. El proceso lee primero los registros remotos, compara solo campos administrados por este contrato y clasifica cada fila local como create, update o unchanged. Los registros que existan únicamente en Airtable permanecen intactos.

## Alcance y orden

| Orden | SQLite | Airtable | Llave | Links resueltos |
| ---: | --- | --- | --- | --- |
| 1 | `cortes_caja` | CortesCaja | `id` -> `id_sqlite` | empleados por `codigo_empleado` |
| 2 | `tickets` | Tickets | `id` -> `id_sqlite` | corte por `id_sqlite`; mesa por `codigo_mesa`; empleado por `codigo_empleado` |
| 3 | `lineas_ticket` | LineasTicket | `id` -> `id_sqlite` | ticket por `id_sqlite`; producto por `sku` |
| 4 | `pagos` | Pagos | `id` -> `id_sqlite` | ticket/corte por `id_sqlite`; método y empleado por llave natural |
| 5 | `trabajos_impresion` | TrabajosImpresion | `id` -> `id_sqlite` | impresora por `clave_impresora`; ticket por `id_sqlite` |
| 6 | `notificaciones_sms` | HistorialSMS | `id` -> `id_sqlite` | canal y empleado por llave natural |
| 7 | `eventos_auditoria` | EventosAuditoria | `id` -> `id_sqlite` | empleado por llave natural; corte/ticket por `id_sqlite` |

En ejecución, las tablas se procesan en ese orden y se replanea cada nivel. Así, los IDs de registros Airtable recién creados están disponibles antes de construir links hijos. En dry-run se usan referencias pendientes internas únicamente para validar la dependencia; nunca se envían a Airtable.

## No soportado en este bloque

| Dominio SQLite | Estado | Motivo |
| --- | --- | --- |
| `lotes_comanda`, `ordenes_estacion`, `lineas_orden_estacion` | No soportado | El schema JSON vigente no contiene LotesComanda ni tablas de órdenes de estación. |
| `movimientos_inventario` | No soportado | MovimientosInventario aparece en documentación de diseño, pero no en `kanpai_airtable_schema.v1.json`. |

Habilitar esos dominios requiere una migración de schema Airtable revisada y aprobada por separado.

## Campos omitidos y límites

- No se exportan PIN, sesiones, payloads de autorización ni tablas no declaradas en `field_map.v1.json`.
- No se exportan relaciones para las que el schema no ofrece campo: orden de estación/lote en trabajos de impresión, recepción de compra en movimientos ni alerta de stock en SMS.
- `idempotency_key` de impresión no tiene columna Airtable en el schema vigente; `id_sqlite` es la llave de upsert y `folio` queda visible para diagnóstico.
- `estado_sync` se marca `Sincronizado`; no se escriben `revision_remota`, `ultimo_pull_en`, `ultimo_push_en`, `actualizado_airtable_en` ni `error_sync`, evitando cambios artificiales en cada corrida.
- Un link requerido sin destino remoto produce error y omite esa fila. Los links opcionales no resueltos generan warning y se envían vacíos, de acuerdo con la nulabilidad local.
- La comparación normaliza números, booleanos, texto y listas de IDs Airtable. Solo se actualizan campos cuyo valor administrado cambió.
- No hay API de delete en el script ni en el cliente reutilizado.

## Operación

Dry-run:

```powershell
uv run python airtable/scripts/push_sqlite_to_airtable.py --dry-run
```

Escritura deliberada:

```powershell
uv run python airtable/scripts/push_sqlite_to_airtable.py --execute --confirm PUSH_SQLITE_TO_AIRTABLE
```

El reporte runtime se genera en `airtable/reports/sqlite_to_airtable_push_report.md`, ruta ignorada por git.
