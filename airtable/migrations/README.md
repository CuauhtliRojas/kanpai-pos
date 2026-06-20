# Migraciones Airtable

Esta carpeta contiene migraciones declarativas tipo Alembic para Airtable.

Reglas:

- Cada migración tiene `revision`.
- Cada migración tiene `down_revision`.
- No se permiten operaciones destructivas por defecto.
- No se borran tablas por script.
- No se borran campos por script.
- Los cambios se aplican con runner y quedan registrados en `_AirtableSchemaMigrations`.
- Todo cambio real exige dry-run previo.
- SQLite solo consume campos declarados en `field_map`.
