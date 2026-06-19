# Kanpai POS

Kanpai POS es un backend local-first para un restaurante bar tipo Tachinomi.

## Stack base

- Python
- FastAPI
- SQLite local
- SQLAlchemy
- Alembic
- uv
- pydantic-settings
- pytest
- ruff

## Arquitectura inicial

SQLite sera la base operativa local para tickets, comandas, pagos, cortes, impresion, inventario operativo y auditoria.

Airtable funcionara como backoffice administrativo para catalogos y como destino de sincronizacion para datos transaccionales/reportes.

## Comandos utiles

Instalar dependencias:

```powershell
uv sync
Levantar API local:

uv run uvicorn app.main:app --reload

Revisar salud:

Invoke-RestMethod http://127.0.0.1:8000/health

Ejecutar tests:

uv run pytest

Ejecutar ruff:

uv run ruff check .

Crear migracion Alembic:

uv run alembic revision --autogenerate -m "initial schema"

Aplicar migraciones:

uv run alembic upgrade head

