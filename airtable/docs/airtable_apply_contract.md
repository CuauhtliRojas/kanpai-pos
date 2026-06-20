# Contrato de aplicación de schema Airtable

## Objetivo

Aplicar el schema declarativo de Kanpai POS sobre una base Airtable existente.

El script no crea la base. La base debe existir y `AIRTABLE_BASE_ID` debe apuntar a ella.

## Permisos requeridos para apply schema

Para inspección y creación de estructura:

- schema.bases:read
- schema.bases:write
- Access a la base Kanpai POS
- Usuario dueño del PAT con permiso Creator sobre la base

## Permisos NO requeridos en esta fase

No se requieren todavía:

- data.records:read
- data.records:write

Esos permisos serán necesarios después para seed/sync de registros.

## Lo que el script puede hacer

- Leer schema de base.
- Crear tablas faltantes.
- Crear campos directos faltantes.
- Crear campos link tardíos después de resolver IDs reales de tablas.
- Crear campos formula tardíos.
- Saltar tablas/campos ya existentes.
- Generar reporte Markdown.
- Ejecutar dry-run sin tocar Airtable.

## Lo que el script NO debe hacer

- No borrar tablas.
- No borrar campos.
- No borrar records.
- No cambiar tipos de campos existentes.
- No limpiar `Table 1`.
- No tocar secretos.
- No escribir datos operativos.
- No ejecutar sin confirmación explícita.

## Table 1

Airtable crea una tabla inicial obligatoria en bases nuevas. Si queda `Table 1`, se deja como tabla bootstrap temporal.

Después de aplicar el schema se puede borrar manualmente desde UI si Airtable lo permite, o renombrar a `_Bootstrap`.

## Rate limit

Airtable limita requests por base. El aplicador debe mantener throttling y manejar HTTP 429 con espera antes de reintentar.
