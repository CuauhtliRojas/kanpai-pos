"""Idempotently remove local development fixtures from the operational catalog."""

from pathlib import Path
import sys

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    DiningTable,
    InventoryItem,
    MenuCategory,
    Product,
    ProductPackage,
    ProductRecipe,
    ProductStationAssignment,
    ProductVariantGroup,
    ProductVariantOption,
    ProductionStation,
)

DEMO_SKUS = (
    "DEV-CHELA",
    "DEV-SAKE",
    "DEV-CHELA-SAKE",
    "DEV-YAKITORI-ORDEN-3",
)


def deactivate_demo_catalog() -> dict[str, int]:
    counts: dict[str, int] = {}
    with SessionLocal() as session:
        products = list(
            session.scalars(select(Product).where(Product.sku.in_(DEMO_SKUS)))
        )
        for product in products:
            product.active = False
            product.visible_pos = False
        counts["products"] = len(products)

        product_ids = [product.id for product in products]
        for label, model in (
            ("recipes", ProductRecipe),
            ("assignments", ProductStationAssignment),
            ("variant_groups", ProductVariantGroup),
        ):
            rows = (
                list(session.scalars(select(model).where(model.product_id.in_(product_ids))))
                if product_ids
                else []
            )
            for row in rows:
                row.active = False
            counts[label] = len(rows)

        groups = (
            list(
                session.scalars(
                    select(ProductVariantGroup).where(
                        ProductVariantGroup.product_id.in_(product_ids)
                    )
                )
            )
            if product_ids
            else []
        )
        group_ids = [group.id for group in groups]
        options = (
            list(
                session.scalars(
                    select(ProductVariantOption).where(
                        ProductVariantOption.variant_group_id.in_(group_ids)
                    )
                )
            )
            if group_ids
            else []
        )
        for option in options:
            option.active = False
        counts["variant_options"] = len(options)

        packages = (
            list(
                session.scalars(
                    select(ProductPackage).where(
                        ProductPackage.package_product_id.in_(product_ids)
                    )
                )
            )
            if product_ids
            else []
        )
        for package in packages:
            package.active = False
            for item in package.items:
                item.active = False
        counts["packages"] = len(packages)

        inventory = list(
            session.scalars(
                select(InventoryItem).where(
                    InventoryItem.item_code.in_(("INV-ARROZ", "INV-SAKE", "INV-LIMON"))
                )
            )
        )
        for item in inventory:
            item.active = False
        counts["inventory_items"] = len(inventory)

        categories = list(
            session.scalars(
                select(MenuCategory).where(
                    MenuCategory.name.in_(("Ramen", "Onigiri", "Cocteleria"))
                )
            )
        )
        for category in categories:
            category.active = False
        counts["categories"] = len(categories)

        stations = list(
            session.scalars(
                select(ProductionStation).where(
                    ProductionStation.station_key == "COCINA"
                )
            )
        )
        for station in stations:
            station.active = False
        counts["stations"] = len(stations)

        tables = list(
            session.scalars(
                select(DiningTable).where(
                    DiningTable.table_code.in_(("B01", "TAKEOUT", "M18", "M19", "M20"))
                )
            )
        )
        for table in tables:
            table.active = False
        counts["tables"] = len(tables)
        session.commit()
    return counts


def main() -> int:
    counts = deactivate_demo_catalog()
    print("Demo catalog disabled: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
