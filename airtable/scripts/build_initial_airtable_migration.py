import json
from pathlib import Path

plan_path = Path("airtable/schema/kanpai_airtable_metadata_plan.v1.json")
out_path = Path("airtable/migrations/0001_initial_schema.json")

plan = json.loads(plan_path.read_text(encoding="utf-8"))

operations = []

for table in plan["tables_to_create"]:
    operations.append({
        "op": "ensure_table",
        "table": table["name"],
        "ownership": table["ownership"],
        "source_table": table.get("source_table"),
        "fields": table["fields"],
    })

for item in plan["fields_to_create_late"]:
    operations.append({
        "op": "ensure_field",
        "table": item["table_name"],
        "field": item["field"],
        "late": True,
    })

migration = {
    "revision": "0001_initial_schema",
    "down_revision": None,
    "description": "Crea schema inicial Airtable Kanpai POS.",
    "schema_version": plan["schema_version"],
    "base_name": plan["base_name"],
    "destructive": False,
    "sqlite_dependency": {
        "required": False,
        "alembic_revision": None
    },
    "operations": operations,
}

out_path.write_text(json.dumps(migration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("MIGRATION OK")
print(f"Salida: {out_path}")
print(f"Operaciones: {len(operations)}")
