# Airtable - Kanpai POS

Esta carpeta contiene el diseño, scripts y documentación de la base Airtable nueva `Kanpai POS`.

## Principio rector

SQLite/FastAPI es la base operativa local-first. Airtable no es runtime crítico de caja.

Airtable se usará para:

- Backoffice administrativo.
- Catálogos editables.
- Configuración operativa.
- Supervisión.
- Espejo de ventas, inventario, cortes, producción, impresión, SMS y auditoría.
- Sincronización controlada por dominio.

## Fases

- 4-A Auditoría.
- 4-B Diseño conceptual Airtable.
- 4-C Schema JSON declarativo.
- 4-D Refactor de scripts Airtable.
- 4-E Creación controlada de base.
- 4-F Plan de sincronización.

## Seguridad

Nunca hardcodear tokens. Usar `.env` para:

```text
AIRTABLE_API_TOKEN
AIRTABLE_BASE_ID
AIRTABLE_WORKSPACE_ID
No guardar PIN, hash de PIN, tokens de sesión, tokens LabsMobile ni secretos en Airtable.
