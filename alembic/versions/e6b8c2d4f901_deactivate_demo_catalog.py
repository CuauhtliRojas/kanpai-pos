"""Deactivate local development catalog rows.

Revision ID: e6b8c2d4f901
Revises: c4d8e2f1a6b9
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e6b8c2d4f901"
down_revision: str | Sequence[str] | None = "c4d8e2f1a6b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEMO_SKUS = (
    "DEV-CHELA",
    "DEV-SAKE",
    "DEV-CHELA-SAKE",
    "DEV-YAKITORI-ORDEN-3",
)
DEMO_ITEM_CODES = ("INV-ARROZ", "INV-SAKE", "INV-LIMON")
DEMO_CATEGORIES = ("Ramen", "Onigiri", "Cocteleria")
DEMO_TABLES = ("B01", "TAKEOUT", "M18", "M19", "M20")


def _in_params(prefix: str, values: tuple[str, ...]) -> tuple[str, dict[str, str]]:
    params = {f"{prefix}_{index}": value for index, value in enumerate(values)}
    placeholders = ", ".join(f":{key}" for key in params)
    return placeholders, params


def upgrade() -> None:
    """Hide demo rows and disable their active runtime relationships."""
    connection = op.get_bind()
    sku_placeholders, sku_params = _in_params("sku", DEMO_SKUS)
    item_placeholders, item_params = _in_params("item", DEMO_ITEM_CODES)
    category_placeholders, category_params = _in_params("category", DEMO_CATEGORIES)
    table_placeholders, table_params = _in_params("table", DEMO_TABLES)

    connection.execute(
        sa.text(
            f"UPDATE productos SET activo = 0, visible_pos = 0 "
            f"WHERE sku IN ({sku_placeholders})"
        ),
        sku_params,
    )
    product_ids = f"SELECT id FROM productos WHERE sku IN ({sku_placeholders})"
    connection.execute(
        sa.text(
            f"UPDATE recetas_producto SET activo = 0 WHERE producto_id IN ({product_ids})"
        ),
        sku_params,
    )
    connection.execute(
        sa.text(
            "UPDATE asignaciones_estacion_producto SET activo = 0 "
            f"WHERE producto_id IN ({product_ids})"
        ),
        sku_params,
    )
    connection.execute(
        sa.text(
            "UPDATE grupos_variante_producto SET activo = 0 "
            f"WHERE producto_id IN ({product_ids})"
        ),
        sku_params,
    )
    connection.execute(
        sa.text(
            "UPDATE opciones_variante_producto SET activo = 0 "
            "WHERE grupo_variante_id IN ("
            "SELECT id FROM grupos_variante_producto "
            f"WHERE producto_id IN ({product_ids}))"
        ),
        sku_params,
    )
    package_ids = (
        "SELECT id FROM paquetes_producto "
        f"WHERE paquete_producto_id IN ({product_ids})"
    )
    connection.execute(
        sa.text(
            "UPDATE componentes_paquete_producto SET activo = 0 "
            f"WHERE paquete_id IN ({package_ids})"
        ),
        sku_params,
    )
    connection.execute(
        sa.text(
            f"UPDATE paquetes_producto SET activo = 0 WHERE id IN ({package_ids})"
        ),
        sku_params,
    )
    connection.execute(
        sa.text(
            f"UPDATE insumos_inventario SET activo = 0 "
            f"WHERE insumo_codigo IN ({item_placeholders})"
        ),
        item_params,
    )
    connection.execute(
        sa.text(
            f"UPDATE categorias_menu SET activo = 0 "
            f"WHERE nombre IN ({category_placeholders})"
        ),
        category_params,
    )
    connection.execute(
        sa.text("UPDATE estaciones_produccion SET activo = 0 WHERE estacion_clave = 'COCINA'")
    )
    connection.execute(
        sa.text(
            f"UPDATE mesas SET activo = 0 WHERE mesa_codigo IN ({table_placeholders})"
        ),
        table_params,
    )


def downgrade() -> None:
    """Keep catalog state unchanged; restoring demo visibility is intentionally manual."""
