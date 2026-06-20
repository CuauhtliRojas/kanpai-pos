import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path("airtable/schema/kanpai_airtable_schema.v1.json")
OUT_PATH = Path("airtable/schema/kanpai_airtable_metadata_plan.v1.json")

DIRECT_TYPES = {
    "singleLineText",
    "multilineText",
    "number",
    "checkbox",
    "singleSelect",
    "dateTime",
}

LATE_TYPES = {
    "link",
    "formula",
}

TYPE_MAP = {
    "singleLineText": "singleLineText",
    "multilineText": "multilineText",
    "number": "number",
    "checkbox": "checkbox",
    "singleSelect": "singleSelect",
    "dateTime": "dateTime",
    "formula": "formula",
    "link": "multipleRecordLinks",
}


def airtable_field_payload(field: dict[str, Any]) -> dict[str, Any]:
    field_type = field["type"]
    payload: dict[str, Any] = {
        "name": field["name"],
        "type": TYPE_MAP[field_type],
    }

    if field_type == "number":
        payload["options"] = {"precision": field.get("precision", 0)}

    if field_type == "singleSelect":
        payload["options"] = {
            "choices": [{"name": option} for option in field.get("options", [])]
        }

    if field_type == "dateTime":
        payload["options"] = {
            "dateFormat": {"name": "iso"},
            "timeFormat": {"name": "24hour"},
            "timeZone": "America/Mexico_City",
        }

    if field_type == "formula":
        payload["options"] = {"formula": field["formula"]}

    if field_type == "link":
        payload["options"] = {
            "linkedTableName": field["target"],
            "linkedTableId": None,
            "prefersSingleRecordLink": not field.get("many", False),
        }

    meta = {}
    for key in ("readonly", "unique", "target", "many"):
        if key in field:
            meta[key] = field[key]
    if meta:
        payload["_kanpai"] = meta

    return payload


def build_plan(schema: dict[str, Any]) -> dict[str, Any]:
    table_names = {table["name"] for table in schema["tables"]}

    tables_to_create = []
    fields_to_create_late = []
    warnings = []

    for table in schema["tables"]:
        fields = table["fields"]
        primary_name = table["primary_field"]
        primary = next(field for field in fields if field["name"] == primary_name)

        create_fields = []

        if primary["type"] == "singleLineText":
            create_fields.append(airtable_field_payload(primary))
            skipped_primary = primary["name"]
        else:
            create_fields.append(
                {
                    "name": "nombre_registro",
                    "type": "singleLineText",
                    "_kanpai": {
                        "generated_primary": True,
                        "reason": f"primary_field original no es singleLineText: {primary_name}",
                        "original_primary_field": primary_name,
                    },
                }
            )
            skipped_primary = None
            warnings.append(
                {
                    "table": table["name"],
                    "warning": "Se genero nombre_registro porque el primary_field no es singleLineText.",
                    "original_primary_field": primary_name,
                    "original_type": primary["type"],
                }
            )

        for field in fields:
            if skipped_primary and field["name"] == skipped_primary:
                continue

            field_type = field["type"]

            if field_type in DIRECT_TYPES:
                create_fields.append(airtable_field_payload(field))
                continue

            if field_type in LATE_TYPES:
                if field_type == "link" and field["target"] not in table_names:
                    raise SystemExit(
                        f"Link invalido: {table['name']}.{field['name']} -> {field['target']}"
                    )

                late_payload = airtable_field_payload(field)
                late_payload["_kanpai"] = {
                    **late_payload.get("_kanpai", {}),
                    "source_table": table["name"],
                    "requires_table_id_resolution": field_type == "link",
                    "requires_existing_fields": field_type == "formula",
                }
                fields_to_create_late.append(
                    {
                        "table_name": table["name"],
                        "field": late_payload,
                    }
                )
                continue

            raise SystemExit(
                f"Tipo no soportado para Metadata plan: {table['name']}.{field['name']} {field_type}"
            )

        tables_to_create.append(
            {
                "name": table["name"],
                "description": table.get("description", ""),
                "source_table": table.get("source_table"),
                "ownership": table["ownership"],
                "fields": create_fields,
            }
        )

    return {
        "schema_version": schema["schema_version"],
        "base_name": schema["base_name"],
        "strategy": {
            "phase_1": "Crear tablas con campos directos.",
            "phase_2": "Resolver table IDs reales.",
            "phase_3": "Crear campos link multipleRecordLinks.",
            "phase_4": "Crear campos formula.",
            "phase_5": "Aplicar vistas/semillas en fases posteriores.",
        },
        "counts": {
            "tables": len(tables_to_create),
            "direct_fields": sum(len(table["fields"]) for table in tables_to_create),
            "late_fields": len(fields_to_create_late),
            "warnings": len(warnings),
        },
        "warnings": warnings,
        "tables_to_create": tables_to_create,
        "fields_to_create_late": fields_to_create_late,
    }


schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
plan = build_plan(schema)

OUT_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("METADATA PLAN OK")
print(f"Salida: {OUT_PATH}")
print(f"Tablas: {plan['counts']['tables']}")
print(f"Campos directos: {plan['counts']['direct_fields']}")
print(f"Campos late: {plan['counts']['late_fields']}")
print(f"Warnings: {plan['counts']['warnings']}")
