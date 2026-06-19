# Fix Alembic INI encoding

## Contexto

Durante la Fase 2-A, los modelos SQLAlchemy, tests y ruff pasaron correctamente:

- `uv run pytest`
- `uv run ruff check .`

El fallo aparecio al ejecutar:

```powershell
uv run alembic revision --autogenerate -m "create catalog and sync base schema"
Error

Alembic no pudo leer alembic.ini porque el archivo quedo guardado con BOM/encoding incompatible para configparser.

Error principal:

configparser.MissingSectionHeaderError: File contains no section headers.
file: WindowsPath('alembic.ini'), line: 1
'ï»¿# A generic, single database configuration.\n'
Causa

PowerShell guardo alembic.ini con una marca BOM que Alembic/configparser interpreto como caracteres visibles antes del comentario inicial.

Correccion

Se reescribio alembic.ini usando .NET con UTF-8 sin BOM:

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path "alembic.ini"), $alembicIni, $utf8NoBom)
Resultado esperado

Despues del fix, Alembic debe poder ejecutar:

uv run alembic revision --autogenerate -m "create catalog and sync base schema"
uv run alembic upgrade head

