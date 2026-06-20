# Estrategia de migraciones Airtable tipo Alembic

## Principio

Airtable no se modifica con un apply global opaco. Se modifica con migraciones JSON versionadas.

## Archivos

- `airtable/schema/kanpai_airtable_schema.v1.json`: contrato deseado.
- `airtable/schema/kanpai_airtable_metadata_plan.v1.json`: plan derivado para Metadata API.
- `airtable/migrations/*.json`: cambios versionados aplicables.
- `airtable/schema/field_map.v1.json`: whitelist de sincronización.
- `airtable/scripts/apply_airtable_migrations.py`: runner.
- `airtable/scripts/check_airtable_drift.py`: verificador de drift.

## Tabla remota de control

El runner crea o usa:

`_AirtableSchemaMigrations`

Campos:

- revision
- down_revision
- checksum
- applied_at
- status
- report

## Operaciones permitidas

- ensure_table
- ensure_field
- ensure_select_option
- rename_field_safe
- create_view futuro
- mark_deprecated futuro

## Operaciones prohibidas por defecto

- delete_table
- delete_field
- destructive_update
- change_field_type automático

## Relación con SQLite

Si SQLite necesita una tabla o columna remota, se crea una migración Airtable.

Si Airtable tiene columnas extra, SQLite las ignora salvo que estén en `field_map`.

## Política de drift

Errores:

- Tabla requerida faltante.
- Campo requerido faltante.
- Tipo requerido cambiado.
- Link requerido roto.

Warnings:

- Campo extra no mapeado.
- Tabla extra no mapeada.
- Table 1 o _Bootstrap presente.

## Bloqueo de edición

La protección real se hace con:

- Permisos de base.
- Permisos de tabla/campo desde UI.
- Interfaces para usuarios no técnicos.
- Vistas que ocultan campos técnicos.
- Drift check semanal.

El script no asume que puede administrar permisos finos de campo desde API.
