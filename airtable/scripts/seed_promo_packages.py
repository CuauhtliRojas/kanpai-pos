from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
for import_path in (ROOT, SCRIPT_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from airtable_records_client import AirtableRecordsClient  # noqa: E402

CONFIRM_TEXT = "SEED_KANPAI_PROMO_PACKAGES"

PACKAGE_CATEGORY_NAME = "Promociones"
SAKE_CATEGORY_NAME = "Sake"
MEZCAL_CATEGORY_NAME = "Bebidas alcohol"
BEER_CATEGORY_NAME = "Cervezas"
BAR_STATION_KEY = "BARRA"
PROMO_CATEGORY_ORDER = 0

CHELA_SAKE_PRICE_CENTS = 8000
CHELA_MEZCAL_PRICE_CENTS = 10000
INTERNAL_SHOT_PRICE_CENTS = 100
SHOT_QTY_BASE = 0.03

SHOT_SAKE_SKU = "SHOT-SAKE-BATEO-1OZ"
SHOT_MEZCAL_SKU = "SHOT-MEZCAL-1OZ"

INSUMO_SAKE_BATEO_CODE = "INS-BEB-013"
INSUMO_MEZCAL_CODE = "INS-BEB-020"

SHORT_NAMES_BY_SKU = {
    "CER-BAR-JA1": "Saporo",
    "CER-BAR-JA2": "Kirin",
    "CER-BAR-ME1": "Carta Blanca",
    "CER-BER-ME2": "Sucia Kanpai",
    "SAK-BAR-001": "Kiku",
    "SAK-BAR-002": "Shiboritate",
    "SAK-BAR-003": "Ginjo",
    "SHOT-SAKE-BATEO-1OZ": "Bateo",
    "SHOT-MEZCAL-1OZ": "Mezcal",
}


@dataclass(frozen=True)
class ProductBrief:
    record_id: str
    sku: str
    name: str


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper())
    return re.sub(r"-+", "-", cleaned).strip("-")


def short_product_name(product: "ProductBrief") -> str:
    if product.sku in SHORT_NAMES_BY_SKU:
        return SHORT_NAMES_BY_SKU[product.sku]

    name = product.name.strip()
    name = re.sub(r"(?i)^cerveza\s+", "", name)
    name = re.sub(r"(?i)\s+junmai\s+sake$", "", name)
    name = re.sub(r"(?i)\s+junmai$", "", name)
    return name.title()


def fields(record: dict[str, Any]) -> dict[str, Any]:
    return record.get("fields", {})


def pending_id(table: str, key: str) -> str:
    return f"PENDING:{table}:{key}"


def key_map(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        value = fields(record).get(key)
        if value is not None:
            result[str(value)] = record
    return result


def category_id_by_name(categories: list[dict[str, Any]], name: str) -> str:
    for record in categories:
        if fields(record).get("nombre") == name:
            return record["id"]
    raise SystemExit(f"No encontré categoría Airtable: {name}")


def ensure_category_id_by_name(
    client: AirtableRecordsClient,
    categories: list[dict[str, Any]],
    name: str,
    execute: bool,
) -> str:
    for record in categories:
        if fields(record).get("nombre") == name:
            return record["id"]

    record = {"nombre": name, "orden": PROMO_CATEGORY_ORDER, "activo": True}
    print(f"Categoría nueva requerida: {name} | {'create' if execute else 'dry-run'}")

    if not execute:
        return pending_id("CategoriasMenu", name)

    created = client.create_records("CategoriasMenu", [record])[0]
    categories.append(created)
    return created["id"]


def station_id_by_key(stations: list[dict[str, Any]], key: str) -> str:
    for record in stations:
        if fields(record).get("clave_estacion") == key:
            return record["id"]
    raise SystemExit(f"No encontré estación Airtable: {key}")


def insumo_id_by_code(insumos: list[dict[str, Any]], code: str) -> str:
    for record in insumos:
        if fields(record).get("codigo_insumo") == code:
            return record["id"]
    raise SystemExit(f"No encontré insumo Airtable: {code}")


def product_briefs_by_category(
    productos: list[dict[str, Any]],
    category_id: str,
) -> list[ProductBrief]:
    result: list[ProductBrief] = []
    for record in productos:
        f = fields(record)
        sku = str(f.get("sku") or "")
        category_ids = list(f.get("categoria") or [])
        if category_id not in category_ids:
            continue
        if f.get("tipo_producto") != "Simple":
            continue
        if not f.get("activo", False):
            continue
        if not f.get("visible_pos", False):
            continue
        result.append(
            ProductBrief(
                record_id=record["id"],
                sku=sku,
                name=str(f.get("nombre_visible") or f.get("nombre") or sku),
            )
        )
    return sorted(result, key=lambda item: item.sku)


def create_many(
    client: AirtableRecordsClient,
    table: str,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    created: list[dict[str, Any]] = []
    for idx in range(0, len(records), 10):
        created.extend(client.create_records(table, records[idx : idx + 10]))
    return created


def product_brief_from_map(
    productos_by_sku: dict[str, dict[str, Any]],
    sku: str,
    fallback_name: str,
) -> ProductBrief:
    record = productos_by_sku[sku]
    f = fields(record)
    return ProductBrief(
        record_id=record["id"],
        sku=sku,
        name=str(f.get("nombre_visible") or f.get("nombre") or fallback_name),
    )


def add_virtual_product(
    productos_by_sku: dict[str, dict[str, Any]],
    sku: str,
    record: dict[str, Any],
) -> None:
    productos_by_sku[sku] = {
        "id": pending_id("Productos", sku),
        "fields": dict(record),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    execute = bool(args.execute)
    if execute and args.confirm != CONFIRM_TEXT:
        raise SystemExit(f"Para ejecutar usa: --execute --confirm {CONFIRM_TEXT}")

    client = AirtableRecordsClient.from_env()

    productos = client.list_records("Productos")
    categorias = client.list_records("CategoriasMenu")
    estaciones = client.list_records("EstacionesProduccion")
    insumos = client.list_records("InsumosInventario")
    recetas = client.list_records("RecetasProducto")
    paquetes = client.list_records("PaquetesProducto")
    componentes = client.list_records("ComponentesPaqueteProducto")

    productos_by_sku = key_map(productos, "sku")
    recetas_by_name = key_map(recetas, "nombre_registro")
    paquetes_by_name = key_map(paquetes, "nombre_registro")
    componentes_by_name = key_map(componentes, "nombre_registro")

    beer_category_id = category_id_by_name(categorias, BEER_CATEGORY_NAME)
    sake_category_id = category_id_by_name(categorias, SAKE_CATEGORY_NAME)
    mezcal_category_id = category_id_by_name(categorias, MEZCAL_CATEGORY_NAME)
    package_category_id = ensure_category_id_by_name(
        client, categorias, PACKAGE_CATEGORY_NAME, execute
    )
    bar_station_id = station_id_by_key(estaciones, BAR_STATION_KEY)

    sake_insumo_id = insumo_id_by_code(insumos, INSUMO_SAKE_BATEO_CODE)
    mezcal_insumo_id = insumo_id_by_code(insumos, INSUMO_MEZCAL_CODE)

    beers = product_briefs_by_category(productos, beer_category_id)
    sake_products = product_briefs_by_category(productos, sake_category_id)

    shot_products = [
        {
            "sku": SHOT_SAKE_SKU,
            "nombre": "Shot sake bateo 1 oz",
            "nombre_visible": "Shot sake bateo 1 oz",
            "tipo_producto": "Simple",
            "precio_centavos": INTERNAL_SHOT_PRICE_CENTS,
            "categoria": [sake_category_id],
            "visible_pos": False,
            "activo": True,
        },
        {
            "sku": SHOT_MEZCAL_SKU,
            "nombre": "Shot mezcal 1 oz",
            "nombre_visible": "Shot mezcal 1 oz",
            "tipo_producto": "Simple",
            "precio_centavos": INTERNAL_SHOT_PRICE_CENTS,
            "categoria": [mezcal_category_id],
            "visible_pos": False,
            "activo": True,
        },
    ]

    shot_products_to_create = [
        record for record in shot_products if record["sku"] not in productos_by_sku
    ]

    print(f"MODE: {'execute' if execute else 'dry-run'}")
    print(f"Categoría de paquetes: {PACKAGE_CATEGORY_NAME}")

    print(f"\nCervezas detectadas: {len(beers)}")
    for item in beers:
        print(f"- {item.sku} | {item.name}")

    print(f"\nSakes visibles detectados: {len(sake_products)}")
    for item in sake_products:
        print(f"- {item.sku} | {item.name}")

    print("\nShots internos requeridos:")
    for record in shot_products:
        status = "exists" if record["sku"] in productos_by_sku else "create"
        print(f"- {record['sku']} | {status}")

    if execute and shot_products_to_create:
        created = create_many(client, "Productos", shot_products_to_create)
        for record in created:
            productos_by_sku[str(fields(record).get("sku"))] = record
    else:
        for record in shot_products_to_create:
            add_virtual_product(productos_by_sku, str(record["sku"]), record)

    recipe_specs = [
        (SHOT_SAKE_SKU, INSUMO_SAKE_BATEO_CODE, sake_insumo_id),
        (SHOT_MEZCAL_SKU, INSUMO_MEZCAL_CODE, mezcal_insumo_id),
    ]

    recipes_to_create = []
    for product_sku, insumo_code, insumo_id in recipe_specs:
        recipe_key = f"{product_sku}|{insumo_code}"
        if recipe_key in recetas_by_name:
            continue

        recipes_to_create.append(
            {
                "nombre_registro": recipe_key,
                "producto": [productos_by_sku[product_sku]["id"]],
                "insumo": [insumo_id],
                "cantidad_base": SHOT_QTY_BASE,
                "porcentaje_merma": 0,
                "activo": True,
            }
        )

    if execute and recipes_to_create:
        create_many(client, "RecetasProducto", recipes_to_create)

    all_sake_components = list(sake_products)
    all_sake_components.append(
        product_brief_from_map(
            productos_by_sku,
            SHOT_SAKE_SKU,
            "Shot sake bateo 1 oz",
        )
    )

    mezcal_component = product_brief_from_map(
        productos_by_sku,
        SHOT_MEZCAL_SKU,
        "Shot mezcal 1 oz",
    )

    package_product_specs: list[dict[str, Any]] = []

    for beer in beers:
        for sake in all_sake_components:
            sku = f"PROMO-CS-{slug(beer.sku)}-{slug(sake.sku)}"
            package_product_specs.append(
                {
                    "sku": sku,
                    "nombre": f"Promo chela + sake: {beer.name} + {sake.name}",
                    "nombre_visible": f"{short_product_name(beer)} + {short_product_name(sake)}",
                    "tipo_producto": "Paquete",
                    "precio_centavos": CHELA_SAKE_PRICE_CENTS,
                    "categoria": [package_category_id],
                    "visible_pos": True,
                    "activo": True,
                    "_components": [beer.sku, sake.sku],
                }
            )

        sku = f"PROMO-CM-{slug(beer.sku)}-{slug(mezcal_component.sku)}"
        package_product_specs.append(
            {
                "sku": sku,
                "nombre": f"Promo chela + mezcal: {beer.name} + {mezcal_component.name}",
                "nombre_visible": (
                    f"{short_product_name(beer)} + {short_product_name(mezcal_component)}"
                ),
                "tipo_producto": "Paquete",
                "precio_centavos": CHELA_MEZCAL_PRICE_CENTS,
                "categoria": [package_category_id],
                "visible_pos": True,
                "activo": True,
                "_components": [beer.sku, mezcal_component.sku],
            }
        )

    products_to_create = [
        {key: value for key, value in spec.items() if not key.startswith("_")}
        for spec in package_product_specs
        if spec["sku"] not in productos_by_sku
    ]

    print(f"\nProductos nuevos a crear: {len(shot_products_to_create) + len(products_to_create)}")
    for record in shot_products_to_create:
        print(f"- Producto shot: {record['sku']}")
    for record in products_to_create:
        print(f"- Producto paquete: {record['sku']} | {record['precio_centavos']}")

    if execute and products_to_create:
        created = create_many(client, "Productos", products_to_create)
        for record in created:
            productos_by_sku[str(fields(record).get("sku"))] = record
    else:
        for record in products_to_create:
            add_virtual_product(productos_by_sku, str(record["sku"]), record)

    package_records_to_create = []
    for spec in package_product_specs:
        package_sku = spec["sku"]
        if package_sku in paquetes_by_name:
            continue

        package_records_to_create.append(
            {
                "nombre_registro": package_sku,
                "producto_paquete": [productos_by_sku[package_sku]["id"]],
                "modo_paquete": "Componentes fijos",
                "comportamiento_impresion": "Imprimir componentes",
                "comportamiento_inventario": "Consumir recetas de componentes",
                "activo": True,
            }
        )

    print(f"\nPaquetesProducto nuevos a crear: {len(package_records_to_create)}")
    for record in package_records_to_create:
        print(f"- {record['nombre_registro']}")

    if execute and package_records_to_create:
        created = create_many(client, "PaquetesProducto", package_records_to_create)
        for record in created:
            paquetes_by_name[str(fields(record).get("nombre_registro"))] = record
    else:
        for record in package_records_to_create:
            key = str(record["nombre_registro"])
            paquetes_by_name[key] = {
                "id": pending_id("PaquetesProducto", key),
                "fields": dict(record),
            }

    component_records_to_create = []
    for spec in package_product_specs:
        package_sku = spec["sku"]
        package_record = paquetes_by_name[package_sku]

        for order, component_sku in enumerate(spec["_components"], start=1):
            component_key = f"{package_sku}|{component_sku}"
            if component_key in componentes_by_name:
                continue

            component_records_to_create.append(
                {
                    "nombre_registro": component_key,
                    "paquete": [package_record["id"]],
                    "producto_componente": [productos_by_sku[component_sku]["id"]],
                    "cantidad": 1,
                    "orden": order,
                    "estacion_override": [bar_station_id],
                    "visible_ticket_cliente": True,
                    "activo": True,
                }
            )

    print(f"\nComponentesPaqueteProducto nuevos a crear: {len(component_records_to_create)}")
    for record in component_records_to_create:
        print(
            f"- {record['nombre_registro']} | orden={record['orden']} "
            f"| cantidad={record['cantidad']}"
        )

    print(f"\nRecetasProducto nuevas a crear: {len(recipes_to_create)}")
    for record in recipes_to_create:
        print(f"- {record['nombre_registro']}")

    if execute and component_records_to_create:
        create_many(client, "ComponentesPaqueteProducto", component_records_to_create)

    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
