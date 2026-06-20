# Scripts Airtable

Aquí vivirán los scripts seguros para crear, inspeccionar, comparar y sembrar la base Airtable `Kanpai POS`.

Reglas:

- No hardcodear tokens.
- No ejecutar cambios destructivos por defecto.
- Todo script de escritura debe soportar dry-run antes de tocar Airtable.
- Todo cambio real debe generar reporte.
- Usar `.env` local para credenciales.

Operación manual y programada: [Manual operativo de sincronización](../docs/airtable_sync_operating_manual.md).
