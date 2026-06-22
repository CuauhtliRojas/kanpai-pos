import argparse
from pathlib import Path

from sqlalchemy import select
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.domain.constants import (
    CatalogStatus,
    ConnectionType,
    ItemType,
    PaymentMethodValue,
    ProductType,
    TableStatus,
    UnitFamily,
    NotificationChannelKey,
)
from app.models import (
    BusinessSetting,
    DiningTable,
    Employee,
    EmployeeRole,
    FolioSequence,
    InventoryItem,
    MenuCategory,
    PaymentMethod,
    Permission,
    PosDevice,
    Printer,
    Product,
    ProductPackage,
    ProductPackageItem,
    ProductRecipe,
    ProductStationAssignment,
    ProductVariantGroup,
    ProductVariantOption,
    ProductionStation,
    Role,
    RolePermission,
    ServiceZone,
    Unit,
    UnitConversion,
    NotificationChannel,
)
from app.services.auth_service import hash_pin, verify_pin
from airtable.scripts.build_airtable_seed import build_seed

REAL_CATALOG_EXCEL = Path("airtable/imports/Kanpai.xlsx")
REAL_CATALOG_FIXED = Path("airtable/seeds/kanpai_fixed_seed.v1.json")


def get_or_create(
    session: Session, model: type, lookup: dict, defaults: dict | None = None
):
    statement = select(model).filter_by(**lookup)
    instance = session.execute(statement).scalar_one_or_none()

    if instance is not None:
        return instance, False

    payload = dict(lookup)

    if defaults:
        payload.update(defaults)

    instance = model(**payload)
    session.add(instance)
    session.flush()

    return instance, True


def upsert_variant_group(
    session: Session,
    product: Product,
    *,
    name: str,
    min_select: int,
    max_select: int,
    required: bool,
    options: list[dict],
) -> ProductVariantGroup:
    """Upsert one product-scoped variant group without removing local data."""
    group, _ = get_or_create(
        session,
        ProductVariantGroup,
        {"product_id": product.id, "name": name},
        {
            "min_select": min_select,
            "max_select": max_select,
            "required": required,
            "active": True,
        },
    )
    group.min_select = min_select
    group.max_select = max_select
    group.required = required
    group.active = True

    for definition in options:
        option, _ = get_or_create(
            session,
            ProductVariantOption,
            {"variant_group_id": group.id, "name": definition["name"]},
            definition,
        )
        option.product_id = definition.get("product_id")
        option.sku = definition.get("sku")
        option.price_delta_cents = definition.get("price_delta_cents", 0)
        option.station_id = definition.get("station_id")
        option.active = definition.get("active", True)
    return group


def seed_business_settings(session: Session) -> None:
    existing = session.execute(select(BusinessSetting).limit(1)).scalar_one_or_none()

    if existing is not None:
        return

    session.add(
        BusinessSetting(
            business_name="Kanpai",
            currency="MXN",
            ticket_message="Gracias por su visita.",
            inventory_enabled=True,
            tax_enabled=True,
            tax_rate_bps=1600,
            tax_included=False,
            tax_label="IVA",
            timezone="America/Mexico_City",
            active=True,
        )
    )


def seed_folio_sequences(session: Session) -> None:
    sequences = [
        ("TICKET", "TK"),
        ("CORTE", "CC"),
        ("PAGO", "PG"),
        ("COMANDA", "CMD"),
        ("MOVIMIENTO", "MOV"),
        ("GASTO", "G"),
        ("IMPRESION", "PRN"),
        ("RECEPCION", "REC"),
    ]

    for sequence_key, prefix in sequences:
        get_or_create(
            session,
            FolioSequence,
            {"sequence_key": sequence_key},
            {"prefix": prefix, "next_number": 1, "padding": 6, "active": True},
        )


def seed_payment_methods(session: Session) -> None:
    methods = [
        (PaymentMethodValue.CASH, "Efectivo", False),
        (PaymentMethodValue.CARD, "Tarjeta", True),
        (PaymentMethodValue.TRANSFER, "Transferencia", True),
    ]

    for method_key, name, requires_reference in methods:
        get_or_create(
            session,
            PaymentMethod,
            {"method_key": method_key},
            {"name": name, "requires_reference": requires_reference, "active": True},
        )


def seed_service_zones_and_tables(session: Session) -> None:
    salon, _ = get_or_create(
        session,
        ServiceZone,
        {"zone_key": "SALON"},
        {"name": "Salon", "sort_order": 1, "active": True},
    )
    barra, _ = get_or_create(
        session,
        ServiceZone,
        {"zone_key": "BARRA"},
        {"name": "Barra", "sort_order": 2, "active": True},
    )
    para_llevar, _ = get_or_create(
        session,
        ServiceZone,
        {"zone_key": "PARA_LLEVAR"},
        {"name": "Para llevar", "sort_order": 3, "active": True},
    )

    for number in range(1, 18):
        table, _ = get_or_create(
            session,
            DiningTable,
            {"table_code": f"M{number:02d}"},
            {
                "display_name": f"Mesa {number}",
                "zone_id": salon.id,
                "buzzer_number": number,
                "sort_order": number,
                "status_cache": TableStatus.FREE,
                "active": True,
            },
        )
        table.display_name = f"Mesa {number}"
        table.zone_id = salon.id
        table.sort_order = number
        table.status_cache = TableStatus.FREE
        table.active = True

    operational_codes = {f"M{number:02d}" for number in range(1, 18)}
    for table in session.scalars(select(DiningTable)):
        if table.table_code not in operational_codes:
            table.active = False



def seed_development_tables(session: Session) -> None:
    zones = {
        zone.zone_key: zone for zone in session.scalars(select(ServiceZone)).all()
    }
    tables = (
        ("B01", "Barra 1", "BARRA", 1),
        ("TAKEOUT", "Para llevar", "PARA_LLEVAR", 1),
        ("M18", "Mesa 18", "SALON", 18),
        ("M19", "Mesa 19", "SALON", 19),
        ("M20", "Mesa 20", "SALON", 20),
    )
    for table_code, display_name, zone_key, sort_order in tables:
        table, _ = get_or_create(
            session,
            DiningTable,
            {"table_code": table_code},
            {
                "display_name": display_name,
                "zone_id": zones[zone_key].id,
                "sort_order": sort_order,
                "status_cache": TableStatus.FREE,
                "active": True,
            },
        )
        table.active = True


def seed_pos_devices(session: Session) -> None:
    get_or_create(
        session,
        PosDevice,
        {"device_name": "POS Principal"},
        {"location_label": "Caja", "is_primary": True, "active": True},
    )


def seed_units(session: Session) -> None:
    units = [
        ("G", "g", UnitFamily.MASS),
        ("KG", "kg", UnitFamily.MASS),
        ("ML", "ml", UnitFamily.VOLUME),
        ("LT", "lt", UnitFamily.VOLUME),
        ("L", "lt (legacy)", UnitFamily.VOLUME),
        ("PZA", "pza", UnitFamily.COUNT),
        ("OZ", "oz", UnitFamily.VOLUME),
    ]

    for unit_key, name, unit_family in units:
        get_or_create(
            session,
            Unit,
            {"unit_key": unit_key},
            {"name": name, "unit_family": unit_family, "active": True},
        )


def seed_unit_conversions(session: Session) -> None:
    """Crea conversiones temporales directas sin duplicar pares existentes."""
    units = {
        unit.unit_key: unit for unit in session.execute(select(Unit)).scalars().all()
    }
    conversions = [
        ("KG", "G", Decimal("1000")),
        ("G", "KG", Decimal("0.001")),
        ("LT", "ML", Decimal("1000")),
        ("ML", "LT", Decimal("0.001")),
        ("L", "ML", Decimal("1000")),
        ("ML", "L", Decimal("0.001")),
        ("OZ", "ML", Decimal("29.573529")),
        ("OZ", "G", Decimal("28.349523")),
    ]
    for from_key, to_key, factor in conversions:
        get_or_create(
            session,
            UnitConversion,
            {
                "from_unit_id": units[from_key].id,
                "to_unit_id": units[to_key].id,
            },
            {"factor": factor, "active": True},
        )


def seed_development_inventory_items(session: Session) -> None:
    """Crea insumos temporales de desarrollo en sus unidades base."""
    units = {
        unit.unit_key: unit for unit in session.execute(select(Unit)).scalars().all()
    }
    items = [
        ("INV-ARROZ", "Arroz desarrollo", "G", 1000),
        ("INV-SAKE", "Sake insumo desarrollo", "ML", 750),
        ("INV-LIMON", "Limon desarrollo", "PZA", 10),
    ]
    for item_code, name, unit_key, minimum_stock_qty in items:
        get_or_create(
            session,
            InventoryItem,
            {"item_code": item_code},
            {
                "name": name,
                "base_unit_id": units[unit_key].id,
                "minimum_stock_qty": minimum_stock_qty,
                "item_type": ItemType.OTHER,
                "active": True,
                "sync_status": CatalogStatus.ACTIVE,
            },
        )


def seed_categories_and_stations(session: Session) -> None:
    categories = [
        ("Bebidas alcohol", 1),
        ("Bebidas sin alcohol", 2),
        ("Cervezas", 3),
        ("Sake", 4),
        ("Refrescos", 5),
        ("Yakitori", 6),
    ]

    for name, sort_order in categories:
        get_or_create(
            session,
            MenuCategory,
            {"name": name},
            {
                "sort_order": sort_order,
                "active": True,
                "sync_status": CatalogStatus.ACTIVE,
            },
        )

    stations = [
        ("COCINA", "Cocina", "COCINA", 1),
        ("BARRA", "Barra", "BARRA", 2),
    ]

    for station_key, name, printer_key, sort_order in stations:
        get_or_create(
            session,
            ProductionStation,
            {"station_key": station_key},
            {
                "name": name,
                "printer_key": printer_key,
                "sort_order": sort_order,
                "active": True,
                "sync_status": CatalogStatus.ACTIVE,
            },
        )
    for station in session.scalars(select(ProductionStation)):
        station.active = station.station_key in {"COCINA", "BARRA"}


def seed_logical_printers(session: Session) -> None:
    """Crea las impresoras lógicas usadas para encolar trabajos locales."""
    stations = {
        station.station_key: station
        for station in session.execute(select(ProductionStation)).scalars()
    }
    printers = [
        ("CAJA", "Caja", None),
        ("COCINA", "Cocina", "COCINA"),
        ("BARRA_FRIA", "Barra fría", "BARRA_FRIA"),
        ("COCTELERIA", "Coctelería", "COCTELERIA"),
        ("BARRA_CALIENTE", "Barra caliente", "BARRA_CALIENTE"),
        ("BARRA", "Barra", "BARRA"),
    ]

    for printer_key, name, station_key in printers:
        station = stations.get(station_key) if station_key else None
        get_or_create(
            session,
            Printer,
            {"printer_key": printer_key},
            {
                "name": name,
                "station_id": station.id if station else None,
                "connection_type": ConnectionType.LOGICAL,
                "active": True,
            },
        )

    for printer in session.scalars(select(Printer)):
        printer.active = printer.printer_key in {"CAJA", "COCINA", "BARRA"}


def seed_development_products(session: Session) -> None:
    """Crea productos temporales para probar captura simple y paquetes."""
    kitchen, _ = get_or_create(
        session,
        ProductionStation,
        {"station_key": "COCINA"},
        {
            "name": "Cocina",
            "printer_key": "COCINA",
            "sort_order": 4,
            "active": False,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )
    kitchen.active = True
    beer_category = session.execute(
        select(MenuCategory).where(MenuCategory.name == "Cervezas")
    ).scalar_one()
    sake_category = session.execute(
        select(MenuCategory).where(MenuCategory.name == "Sake")
    ).scalar_one()
    cold_bar = session.execute(
        select(ProductionStation).where(ProductionStation.station_key == "BARRA")
    ).scalar_one()
    hot_bar = cold_bar
    yakitori_category = session.execute(
        select(MenuCategory).where(MenuCategory.name == "Yakitori")
    ).scalar_one()
    beer, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-CHELA"},
        {
            "product_type": ProductType.SIMPLE,
            "name": "Chela desarrollo",
            "display_name": "Chela desarrollo",
            "category_id": beer_category.id,
            "price_cents": 7_000,
            "active": True,
            "visible_pos": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )
    sake, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-SAKE"},
        {
            "product_type": ProductType.SIMPLE,
            "name": "Sake desarrollo",
            "display_name": "Sake desarrollo",
            "category_id": sake_category.id,
            "price_cents": 6_000,
            "active": True,
            "visible_pos": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )
    package_product, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-CHELA-SAKE"},
        {
            "product_type": ProductType.PACKAGE,
            "name": "Chela + Sake",
            "display_name": "Chela + Sake",
            "category_id": beer_category.id,
            "price_cents": 12_000,
            "active": True,
            "visible_pos": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )
    yakitori, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-YAKITORI-ORDEN-3"},
        {
            "product_type": ProductType.SIMPLE,
            "name": "Orden yakitori 3 piezas",
            "display_name": "Orden yakitori 3 piezas",
            "category_id": yakitori_category.id,
            "price_cents": 15_000,
            "inventory_recipe_multiplier": Decimal("3"),
            "active": True,
            "visible_pos": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )

    for product, station in ((beer, cold_bar), (sake, hot_bar)):
        get_or_create(
            session,
            ProductStationAssignment,
            {"product_id": product.id, "station_id": station.id},
            {"is_primary": True, "active": True, "sync_status": CatalogStatus.ACTIVE},
        )
    get_or_create(
        session, ProductStationAssignment,
        {"product_id": yakitori.id, "station_id": kitchen.id},
        {"is_primary": True, "active": True, "sync_status": CatalogStatus.ACTIVE},
    )
    upsert_variant_group(
        session,
        yakitori,
        name="BROCHETAS",
        min_select=3,
        max_select=3,
        required=True,
        options=[
            {"name": "Pollo", "price_delta_cents": 0, "active": True},
            {"name": "Pulpo", "price_delta_cents": 0, "active": True},
            {"name": "Verduras", "price_delta_cents": 0, "active": True},
        ],
    )
    package, _ = get_or_create(
        session,
        ProductPackage,
        {"package_product_id": package_product.id},
        {"active": True, "sync_status": CatalogStatus.ACTIVE},
    )
    get_or_create(
        session,
        ProductPackageItem,
        {"package_id": package.id, "component_product_id": beer.id},
        {
            "quantity": 1,
            "sort_order": 1,
            "active": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )
    get_or_create(
        session,
        ProductPackageItem,
        {"package_id": package.id, "component_product_id": sake.id},
        {
            "quantity": 1,
            "sort_order": 2,
            "station_id_override": hot_bar.id,
            "active": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )


def seed_development_recipes(session: Session) -> None:
    """Crea recetas temporales e idempotentes para validar consumo por venta."""
    sake_item = session.execute(
        select(InventoryItem).where(InventoryItem.item_code == "INV-SAKE")
    ).scalar_one()
    quantities = {"DEV-CHELA": 100, "DEV-SAKE": 120}
    for sku, quantity_base in quantities.items():
        product = session.execute(
            select(Product).where(Product.sku == sku)
        ).scalar_one()
        get_or_create(
            session,
            ProductRecipe,
            {
                "product_id": product.id,
                "inventory_item_id": sake_item.id,
            },
            {
                "quantity_base": quantity_base,
                "waste_pct": 0,
                "active": True,
                "sync_status": CatalogStatus.ACTIVE,
            },
        )


def seed_real_catalog(session: Session) -> None:
    """Upsert the normalized Excel catalog without inventing missing recipes."""
    result = build_seed(REAL_CATALOG_EXCEL, REAL_CATALOG_FIXED)
    if not result.excel_present:
        raise FileNotFoundError(f"No existe el catálogo real: {REAL_CATALOG_EXCEL}")

    units = {unit.unit_key: unit for unit in session.scalars(select(Unit))}
    for record in result.tables["InsumosInventario"]:
        unit_key = record["unidad_base"][0]
        item, _ = get_or_create(
            session,
            InventoryItem,
            {"item_code": record["codigo_insumo"]},
            {
                "name": record["nombre"],
                "base_unit_id": units[unit_key].id,
                "item_type": record["tipo_insumo"],
                "minimum_stock_qty": Decimal(str(record["stock_minimo"])),
                "unit_cost_cents": record["costo_unitario_centavos"],
                "active": True,
            },
        )
        item.name = record["nombre"]
        item.base_unit_id = units[unit_key].id
        item.item_type = record["tipo_insumo"]
        item.minimum_stock_qty = Decimal(str(record["stock_minimo"]))
        item.unit_cost_cents = record["costo_unitario_centavos"]
        item.active = True
        item.sync_status = CatalogStatus.ACTIVE

    categories = {
        category.name: category for category in session.scalars(select(MenuCategory))
    }
    for record in result.tables["CategoriasMenu"]:
        category, _ = get_or_create(
            session,
            MenuCategory,
            {"name": record["nombre"]},
            {"sort_order": record["orden"]},
        )
        category.active = bool(record["activo"])
        categories[category.name] = category

    products: dict[str, Product] = {}
    for record in result.tables["Productos"]:
        product, _ = get_or_create(
            session,
            Product,
            {"sku": record["sku"]},
            {
                "product_type": ProductType.SIMPLE,
                "name": record["nombre"],
                "display_name": record["nombre_visible"],
                "price_cents": record["precio_centavos"],
                "active": bool(record["activo"]),
                "visible_pos": bool(record["visible_pos"]),
            },
        )
        product.product_type = ProductType.SIMPLE
        product.name = record["nombre"]
        product.variant = record["variante"] or None
        product.display_name = record["nombre_visible"]
        product.category_id = categories[record["categoria"][0]].id
        product.price_cents = record["precio_centavos"]
        product.inventory_recipe_multiplier = Decimal(
            str(record["multiplicador_receta_inventario"])
        )
        product.active = bool(record["activo"])
        product.visible_pos = bool(record["visible_pos"])
        product.sync_status = CatalogStatus.ACTIVE
        products[product.sku] = product
    session.flush()

    stations = {
        station.station_key: station
        for station in session.scalars(select(ProductionStation))
    }
    for record in result.tables["AsignacionesProductoEstacion"]:
        assignment, _ = get_or_create(
            session,
            ProductStationAssignment,
            {
                "product_id": products[record["producto"][0]].id,
                "station_id": stations[record["estacion"][0]].id,
            },
        )
        assignment.is_primary = True
        assignment.active = True

    items = {
        item.item_code: item for item in session.scalars(select(InventoryItem))
    }
    for record in result.tables["RecetasProducto"]:
        recipe, _ = get_or_create(
            session,
            ProductRecipe,
            {
                "product_id": products[record["producto"][0]].id,
                "inventory_item_id": items[record["insumo"][0]].id,
            },
            {
                "quantity_base": Decimal(str(record["cantidad_base"])),
                "waste_pct": Decimal(str(record["porcentaje_merma"])),
                "active": True,
            },
        )
        recipe.quantity_base = Decimal(str(record["cantidad_base"]))
        recipe.waste_pct = Decimal(str(record["porcentaje_merma"]))
        recipe.active = True
        recipe.sync_status = CatalogStatus.ACTIVE


    combo_groups: dict[tuple[str, str], ProductVariantGroup] = {}
    for record in result.tables.get("GruposVarianteProducto", []):
        product = products[record["producto"][0]]
        group = upsert_variant_group(
            session,
            product,
            name=record["nombre"],
            min_select=int(record["seleccion_minima"]),
            max_select=int(record["seleccion_maxima"]),
            required=bool(record["requerido"]),
            options=[],
        )
        group.active = bool(record["activo"])
        combo_groups[(product.sku, record["nombre"])] = group

    for record in result.tables.get("OpcionesVarianteProducto", []):
        group_reference = record["grupo_variante"][0]
        if not isinstance(group_reference, (list, tuple)) or len(group_reference) != 2:
            raise ValueError(
                "El seed requiere grupo_variante como (producto, nombre)."
            )
        group = combo_groups[(group_reference[0], group_reference[1])]
        option_product_sku = next(iter(record["producto_opcional"]), None)
        option_product = products.get(option_product_sku)
        option, _ = get_or_create(
            session,
            ProductVariantOption,
            {"variant_group_id": group.id, "name": record["nombre"]},
            {
                "product_id": option_product.id if option_product else None,
                "sku": record["sku"],
                "price_delta_cents": int(record["diferencia_precio_centavos"]),
                "active": bool(record["activo"]),
            },
        )
        option.product_id = option_product.id if option_product else None
        option.sku = record["sku"]
        option.price_delta_cents = int(record["diferencia_precio_centavos"])
        option.active = bool(record["activo"])

def seed_roles_permissions_and_admin(session: Session) -> None:
    permission_defs = [
        ("DISCOUNT_AUTHORIZE", "Autorizar descuentos"),
        ("TICKET_CANCEL", "Cancelar tickets o lineas"),
        ("CASH_SHIFT_OPEN", "Abrir corte de caja"),
        ("CASH_SHIFT_CLOSE", "Cerrar corte de caja"),
        ("EXPENSE_CREATE", "Registrar gastos"),
        ("INVENTORY_ADJUST", "Ajustar inventario"),
        ("REPRINT", "Autorizar reimpresiones"),
        ("SMS_SEND", "Enviar notificaciones SMS"),
        ("SUPPORT_ACCESS", "Consultar diagnóstico y soporte local"),
        ("ADMIN_READ", "Consultar configuración administrativa"),
    ]

    permissions: dict[str, Permission] = {}

    for permission_key, description in permission_defs:
        permission, _ = get_or_create(
            session,
            Permission,
            {"permission_key": permission_key},
            {
                "description": description,
                "active": True,
                "sync_status": CatalogStatus.ACTIVE,
            },
        )
        permissions[permission_key] = permission

    role_defs = {
        "ADMIN": [
            "DISCOUNT_AUTHORIZE",
            "TICKET_CANCEL",
            "CASH_SHIFT_OPEN",
            "CASH_SHIFT_CLOSE",
            "EXPENSE_CREATE",
            "INVENTORY_ADJUST",
            "REPRINT",
            "SMS_SEND",
            "SUPPORT_ACCESS",
            "ADMIN_READ",
        ],
        "GERENTE": [
            "DISCOUNT_AUTHORIZE",
            "TICKET_CANCEL",
            "CASH_SHIFT_OPEN",
            "CASH_SHIFT_CLOSE",
            "EXPENSE_CREATE",
            "REPRINT",
        ],
        "CAJERO": ["CASH_SHIFT_OPEN", "EXPENSE_CREATE"],
        "ALMACEN": ["INVENTORY_ADJUST"],
        "SOPORTE": ["SUPPORT_ACCESS", "ADMIN_READ"],
    }

    roles: dict[str, Role] = {}

    for role_key, permission_keys in role_defs.items():
        role, _ = get_or_create(
            session,
            Role,
            {"role_key": role_key},
            {
                "name": role_key.title(),
                "active": True,
                "sync_status": CatalogStatus.ACTIVE,
            },
        )
        roles[role_key] = role

        for permission_key in permission_keys:
            get_or_create(
                session,
                RolePermission,
                {"role_id": role.id, "permission_id": permissions[permission_key].id},
            )

    admin, _ = get_or_create(
        session,
        Employee,
        {"employee_code": "ADMIN"},
        {
            "full_name": "Administrador Kanpai",
            "pos_alias": "Admin",
            "active": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )

    get_or_create(
        session,
        EmployeeRole,
        {"employee_id": admin.id, "role_id": roles["ADMIN"].id},
    )
    configured_pin = get_settings().kanpai_admin_pin
    if not admin.pin_hash or not verify_pin(configured_pin, admin.pin_hash):
        admin.pin_hash = hash_pin(configured_pin)
    admin.pin_enabled = True

    for employee in session.scalars(select(Employee)):
        employee.active = employee.id == admin.id


def seed_development_admin(session: Session) -> None:
    """Keep legacy test fixtures isolated from the one-operator production seed."""
    admin_role = session.scalar(select(Role).where(Role.role_key == "ADMIN"))
    employee, _ = get_or_create(
        session,
        Employee,
        {"employee_code": "EMP-0001"},
        {
            "full_name": "Administrador QA",
            "pos_alias": "Admin QA",
            "active": True,
            "sync_status": CatalogStatus.ACTIVE,
        },
    )
    employee.active = True
    employee.pin_hash = hash_pin(get_settings().kanpai_admin_pin)
    employee.pin_enabled = True
    get_or_create(
        session,
        EmployeeRole,
        {"employee_id": employee.id, "role_id": admin_role.id},
    )
    for printer in session.scalars(
        select(Printer).where(
            Printer.printer_key.in_(("BARRA_FRIA", "COCTELERIA", "BARRA_CALIENTE"))
        )
    ):
        printer.active = True


def seed_notification_channels(session: Session) -> None:
    """Crea el canal lógico SMS sin almacenar credenciales del proveedor."""
    get_or_create(
        session, NotificationChannel, {"channel_key": NotificationChannelKey.SMS},
        {"name": "SMS LabsMobile", "active": True},
    )


def run_seed(*, include_development_data: bool = False) -> None:
    with SessionLocal() as session:
        seed_business_settings(session)
        seed_folio_sequences(session)
        seed_payment_methods(session)
        seed_service_zones_and_tables(session)
        seed_pos_devices(session)
        seed_units(session)
        seed_unit_conversions(session)
        seed_categories_and_stations(session)
        seed_logical_printers(session)
        seed_real_catalog(session)
        seed_roles_permissions_and_admin(session)
        if include_development_data:
            seed_development_tables(session)
            seed_development_inventory_items(session)
            seed_development_products(session)
            seed_development_recipes(session)
            _activate_development_catalog(session)
            seed_development_admin(session)
        else:
            _deactivate_development_catalog(session)
        seed_notification_channels(session)
        session.commit()


def _activate_development_catalog(session: Session) -> None:
    """Enable test-only catalog rows, including rows disabled by the QA migration."""
    demo_skus = (
        "DEV-CHELA",
        "DEV-SAKE",
        "DEV-CHELA-SAKE",
        "DEV-YAKITORI-ORDEN-3",
    )
    demo_item_codes = ("INV-ARROZ", "INV-SAKE", "INV-LIMON")
    products = list(session.scalars(select(Product).where(Product.sku.in_(demo_skus))))
    for product in products:
        product.active = True
        product.visible_pos = True

    for item in session.scalars(
        select(InventoryItem).where(InventoryItem.item_code.in_(demo_item_codes))
    ):
        item.active = True

    product_ids = [product.id for product in products]
    if not product_ids:
        return
    for model in (ProductRecipe, ProductStationAssignment, ProductVariantGroup):
        for row in session.scalars(select(model).where(model.product_id.in_(product_ids))):
            row.active = True
    for package in session.scalars(
        select(ProductPackage).where(ProductPackage.package_product_id.in_(product_ids))
    ):
        package.active = True
        for item in package.items:
            item.active = True
    group_ids = list(
        session.scalars(
            select(ProductVariantGroup.id).where(
                ProductVariantGroup.product_id.in_(product_ids)
            )
        )
    )
    if group_ids:
        for option in session.scalars(
            select(ProductVariantOption).where(
                ProductVariantOption.variant_group_id.in_(group_ids)
            )
        ):
            option.active = True


def _deactivate_development_catalog(session: Session) -> None:
    demo_skus = (
        "DEV-CHELA", "DEV-SAKE", "DEV-CHELA-SAKE", "DEV-YAKITORI-ORDEN-3"
    )
    demo_item_codes = ("INV-ARROZ", "INV-SAKE", "INV-LIMON")
    for product in session.scalars(select(Product).where(Product.sku.in_(demo_skus))):
        product.active = False
        product.visible_pos = False
    for item in session.scalars(
        select(InventoryItem).where(InventoryItem.item_code.in_(demo_item_codes))
    ):
        item.active = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-development-data", action="store_true")
    args = parser.parse_args()
    run_seed(include_development_data=args.include_development_data)
    mode = "con fixtures de desarrollo" if args.include_development_data else "sin catalogo demo"
    print(f"Seed operativo aplicado correctamente ({mode}).")
