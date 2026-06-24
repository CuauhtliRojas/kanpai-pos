# Airtable / SQLite — Propiedad de dominio y reset productivo

## Modelo maestro-maestro por dominio

Airtable y SQLite son maestro-maestro, pero cada tabla tiene **una sola dirección**
definida en `airtable/schema/field_map.v1.json`. No existe sincronización bidireccional
libre; todo flujo es upsert sin deletes automáticos.

| Dominio | Maestro | Dirección en field_map |
|---|---|---|
| Catálogo / configuración | **Airtable** | `pull_to_sqlite` |
| Operación local (tickets, pagos, cortes…) | **SQLite** | `push_to_airtable_readonly` |

### Airtable domina catálogo y configuración

Estas tablas se leen de Airtable y se escriben en SQLite mediante `pull_airtable_to_sqlite.py`:

- `ConfiguracionNegocio`, `MetodosPago`, `ZonasServicio`, `Mesas`
- `EstacionesProduccion`, `Impresoras`, `Roles`, `Empleados`
- `CategoriasMenu`, `Productos`, `AsignacionesProductoEstacion`
- `Unidades`, `InsumosInventario`, `RecetasProducto`
- `CanalesNotificacion`, `DescuentosPredeterminados`
- `GruposVarianteProducto`, `OpcionesVarianteProducto`

Para retirar un elemento del catálogo se usa `activo=false` o `visible_pos=false`
en Airtable; nunca borrar el registro.

### SQLite domina operación local

Estas tablas nacen en SQLite y se espejean en Airtable como solo-lectura mediante
`push_sqlite_to_airtable.py`. Airtable no edita estas tablas:

- `CortesCaja`, `Tickets`, `LineasTicket`, `Pagos`
- `TrabajosImpresion`, `HistorialSMS`, `EventosAuditoria`

## El push normal es upsert no destructivo

`push_sqlite_to_airtable.py` solo llama `create_records` y `update_records`.
**Nunca llama `delete_records`**, incluso si existen registros en Airtable que
ya no existen en SQLite. El comentario en `apply_plan` es explícito:

```python
def apply_plan(client, plan):
    """Apply only creates/updates; this API deliberately has no delete path."""
```

Esto significa que si se hace un reset SQLite sin hacer el reset Airtable primero,
los registros huérfanos quedan en Airtable sin afectar la operación.

## Reset Airtable operativo — operación especial

El borrado de registros operativos en Airtable solo existe en
`airtable/scripts/prepare_airtable_production_reset.py`.

Protecciones:

- Modo default es **preview** — lista cuántos registros se borrarían por tabla, sin mutar.
- Para borrar se requiere `--execute --confirm PREPARE_KANPAI_AIRTABLE_PRODUCTION_RESET`.
- La allowlist está codificada explícitamente y se valida contra `field_map.v1.json`:
  cada tabla debe tener `direction == push_to_airtable_readonly`.
- Cualquier tabla con `direction == pull_to_sqlite` (catálogo) es **bloqueada**.
- El script no toca SQLite, no llama pull ni push.

## Orden recomendado para reset productivo integral

Ejecutar en este orden para garantizar coherencia entre SQLite y Airtable:

1. **Cerrar app / backend / worker** — ningún proceso debe escribir en SQLite ni en
   Airtable durante el reset.

2. **Reset SQLite** (operación ya validada en commit `229bd44`):
   ```powershell
   uv run python scripts/prepare_production_database.py
   uv run python scripts/prepare_production_database.py --execute --confirm PREPARE_KANPAI_PRODUCTION_DATABASE
   ```

3. **Preview reset Airtable** — verificar qué se borrará:
   ```powershell
   uv run python airtable/scripts/prepare_airtable_production_reset.py
   ```

4. **Execute reset Airtable** — ⚠️ NO ejecutar sin haber revisado el preview:
   ```powershell
   uv run python airtable/scripts/prepare_airtable_production_reset.py \
       --execute --confirm PREPARE_KANPAI_AIRTABLE_PRODUCTION_RESET
   ```

5. **Pull catálogo Airtable → SQLite** — restablece catálogo limpio:
   ```powershell
   uv run python airtable/scripts/pull_airtable_to_sqlite.py --dry-run
   uv run python airtable/scripts/pull_airtable_to_sqlite.py --execute --confirm PULL_AIRTABLE_TO_SQLITE
   ```

6. **Carga inventario inicial** (si aplica) con `paid_amount_cents = 0` — mediante
   el script de seed o entrada manual en SQLite antes de abrir operación.

7. **Push espejo operativo** (opcional — solo si hay datos operativos iniciales):
   ```powershell
   uv run python airtable/scripts/push_sqlite_to_airtable.py --dry-run
   uv run python airtable/scripts/push_sqlite_to_airtable.py --execute --confirm PUSH_SQLITE_TO_AIRTABLE
   ```

## Verificación post-reset

```powershell
uv run python airtable/scripts/check_airtable_drift.py
uv run python airtable/scripts/pull_airtable_to_sqlite.py --dry-run
uv run python airtable/scripts/push_sqlite_to_airtable.py --dry-run
uv run python scripts/check_pre_sync_invariants.py
```

Los cuatro comandos deben terminar sin errores ni warnings antes de reabrir operación.
