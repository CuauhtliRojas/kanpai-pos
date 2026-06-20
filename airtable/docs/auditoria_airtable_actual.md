
Auditoría Airtable actual - Fase 4-A
Estado del repo

El backend local-first está en estado válido para iniciar diseño Airtable.

Validaciones reportadas:

PRE-SYNC PREFLIGHT: OK
pytest crítico: 10 passed
ruff: All checks passed
Estado Airtable dentro del repo

No existe todavía carpeta airtable/ ni schema declarativo versionado dentro del repo.

El script viejo apply_base_schema.py está fuera del repo actual y funciona como antecedente, pero debe reemplazarse/refactorizarse antes de crear la base nueva.

Limitaciones del script viejo

El script viejo puede:

Crear tablas vía Airtable Metadata API.
Crear campos.
Renombrar campos.

Pero no tiene todavía:

dry-run.
diff contra base existente.
backup/export de schema actual.
validación fuerte de linked records.
validación de select options.
modo no destructivo por defecto.
reporte Markdown post-ejecución.
separación create-only/update-safe.
lectura de schema declarativo canónico.
Decisión

No se debe ejecutar creación real de base hasta terminar:

Diseño conceptual.
Schema JSON declarativo.
Refactor seguro de scripts.
Dry-run.
Aprobación explícita.
