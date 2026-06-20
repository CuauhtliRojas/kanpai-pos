import json
from pathlib import Path

SCHEMA_PATH = Path("airtable/schema/kanpai_airtable_schema.v1.json")
ALLOWED_OWNERSHIP = {
    "AIRTABLE_MASTER",
    "SQLITE_MASTER",
    "BIDIRECTIONAL_CONTROLLED",
    "READONLY_MIRROR",
    "LOCAL_ONLY",
}
ALLOWED_TYPES = {
    "singleLineText",
    "multilineText",
    "number",
    "checkbox",
    "singleSelect",
    "link",
    "dateTime",
    "formula",
}


def fail(message: str) -> None:
    raise SystemExit(f"SCHEMA INVALIDO: {message}")


schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

if not schema.get("base_name"):
    fail("Falta base_name.")

tables = schema.get("tables")
if not isinstance(tables, list) or not tables:
    fail("Falta lista de tablas.")

table_names = [table.get("name") for table in tables]
table_keys = [table.get("key") for table in tables]

if len(table_names) != len(set(table_names)):
    fail("Hay nombres de tabla duplicados.")
if len(table_keys) != len(set(table_keys)):
    fail("Hay keys de tabla duplicadas.")

table_name_set = set(table_names)

for table in tables:
    name = table.get("name")
    key = table.get("key")
    ownership = table.get("ownership")
    fields = table.get("fields")

    if not key or not name:
        fail(f"Tabla sin key/name: {table}")
    if ownership not in ALLOWED_OWNERSHIP:
        fail(f"{name}: ownership invalido {ownership}")
    if not isinstance(fields, list) or not fields:
        fail(f"{name}: sin campos")

    field_names = [field.get("name") for field in fields]
    if len(field_names) != len(set(field_names)):
        fail(f"{name}: campos duplicados")

    primary_field = table.get("primary_field")
    if primary_field not in field_names:
        fail(f"{name}: primary_field no existe: {primary_field}")

    for item in fields:
        field_name = item.get("name")
        field_type = item.get("type")
        if not field_name:
            fail(f"{name}: campo sin nombre")
        if field_type not in ALLOWED_TYPES:
            fail(f"{name}.{field_name}: tipo invalido {field_type}")
        if field_type == "singleSelect":
            options = item.get("options")
            if not isinstance(options, list) or not options:
                fail(f"{name}.{field_name}: singleSelect sin options")
        if field_type == "link":
            target = item.get("target")
            if target not in table_name_set:
                fail(f"{name}.{field_name}: link target inexistente: {target}")
        if field_type == "formula" and not item.get("formula"):
            fail(f"{name}.{field_name}: formula sin expresion")

print("SCHEMA OK")
print(f"Base: {schema['base_name']}")
print(f"Tablas: {len(tables)}")
print(f"Campos: {sum(len(table['fields']) for table in tables)}")
