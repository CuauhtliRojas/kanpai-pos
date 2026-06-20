from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    BusinessSetting,
    DiningTable,
    Employee,
    EmployeeRole,
    FolioSequence,
    MenuCategory,
    PaymentMethod,
    Permission,
    PosDevice,
    Printer,
    Product,
    ProductPackage,
    ProductPackageItem,
    ProductStationAssignment,
    ProductionStation,
    Role,
    RolePermission,
    ServiceZone,
    Unit,
)


def get_or_create(session: Session, model: type, lookup: dict, defaults: dict | None = None):
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
        ("CASH", "Efectivo", False),
        ("CARD", "Tarjeta", True),
        ("TRANSFER", "Transferencia", True),
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

    for number in range(2, 21):
        get_or_create(
            session,
            DiningTable,
            {"table_code": f"M{number:02d}"},
            {
                "display_name": f"Mesa {number}",
                "zone_id": salon.id,
                "buzzer_number": number,
                "sort_order": number,
                "status_cache": "FREE",
                "active": True,
            },
        )

    get_or_create(
        session,
        DiningTable,
        {"table_code": "B01"},
        {
            "display_name": "Barra 1",
            "zone_id": barra.id,
            "sort_order": 1,
            "status_cache": "FREE",
            "active": True,
        },
    )

    get_or_create(
        session,
        DiningTable,
        {"table_code": "TAKEOUT"},
        {
            "display_name": "Para llevar",
            "zone_id": para_llevar.id,
            "sort_order": 1,
            "status_cache": "FREE",
            "active": True,
        },
    )


def seed_pos_devices(session: Session) -> None:
    get_or_create(
        session,
        PosDevice,
        {"device_name": "POS Principal"},
        {"location_label": "Caja", "is_primary": True, "active": True},
    )


def seed_units(session: Session) -> None:
    units = [
        ("G", "g", "MASS"),
        ("KG", "kg", "MASS"),
        ("ML", "ml", "VOLUME"),
        ("L", "lt", "VOLUME"),
        ("PZA", "pza", "COUNT"),
        ("OZ", "oz", "VOLUME"),
    ]

    for unit_key, name, unit_family in units:
        get_or_create(
            session,
            Unit,
            {"unit_key": unit_key},
            {"name": name, "unit_family": unit_family, "active": True},
        )


def seed_categories_and_stations(session: Session) -> None:
    categories = [
        ("Yakitori", 1),
        ("Ramen", 2),
        ("Onigiri", 3),
        ("Cervezas", 4),
        ("Sake", 5),
        ("Cocteleria", 6),
        ("Refrescos", 7),
    ]

    for name, sort_order in categories:
        get_or_create(
            session,
            MenuCategory,
            {"name": name},
            {"sort_order": sort_order, "active": True, "sync_status": "ACTIVE"},
        )

    stations = [
        ("COCINA", "Cocina", "COCINA", 1),
        ("BARRA_FRIA", "Barra fria", "BARRA_FRIA", 2),
        ("COCTELERIA", "Cocteleria", "COCTELERIA", 3),
        ("BARRA_CALIENTE", "Barra caliente", "BARRA_CALIENTE", 4),
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
                "sync_status": "ACTIVE",
            },
        )


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
                "connection_type": "LOGICAL",
                "active": True,
            },
        )


def seed_development_products(session: Session) -> None:
    """Crea productos temporales para probar captura simple y paquetes."""
    beer_category = session.execute(
        select(MenuCategory).where(MenuCategory.name == "Cervezas")
    ).scalar_one()
    sake_category = session.execute(
        select(MenuCategory).where(MenuCategory.name == "Sake")
    ).scalar_one()
    cold_bar = session.execute(
        select(ProductionStation).where(
            ProductionStation.station_key == "BARRA_FRIA"
        )
    ).scalar_one()
    hot_bar = session.execute(
        select(ProductionStation).where(
            ProductionStation.station_key == "BARRA_CALIENTE"
        )
    ).scalar_one()

    beer, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-CHELA"},
        {
            "product_type": "SIMPLE",
            "name": "Chela desarrollo",
            "display_name": "Chela desarrollo",
            "category_id": beer_category.id,
            "price_cents": 7_000,
            "active": True,
            "visible_pos": True,
            "sync_status": "ACTIVE",
        },
    )
    sake, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-SAKE"},
        {
            "product_type": "SIMPLE",
            "name": "Sake desarrollo",
            "display_name": "Sake desarrollo",
            "category_id": sake_category.id,
            "price_cents": 6_000,
            "active": True,
            "visible_pos": True,
            "sync_status": "ACTIVE",
        },
    )
    package_product, _ = get_or_create(
        session,
        Product,
        {"sku": "DEV-CHELA-SAKE"},
        {
            "product_type": "PACKAGE",
            "name": "Chela + Sake",
            "display_name": "Chela + Sake",
            "category_id": beer_category.id,
            "price_cents": 12_000,
            "active": True,
            "visible_pos": True,
            "sync_status": "ACTIVE",
        },
    )

    for product, station in ((beer, cold_bar), (sake, hot_bar)):
        get_or_create(
            session,
            ProductStationAssignment,
            {"product_id": product.id, "station_id": station.id},
            {"is_primary": True, "active": True, "sync_status": "ACTIVE"},
        )

    package, _ = get_or_create(
        session,
        ProductPackage,
        {"package_product_id": package_product.id},
        {"active": True, "sync_status": "ACTIVE"},
    )
    get_or_create(
        session,
        ProductPackageItem,
        {"package_id": package.id, "component_product_id": beer.id},
        {"quantity": 1, "sort_order": 1, "active": True, "sync_status": "ACTIVE"},
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
            "sync_status": "ACTIVE",
        },
    )

def seed_roles_permissions_and_admin(session: Session) -> None:
    permission_defs = [
        ("DISCOUNT_AUTHORIZE", "Autorizar descuentos"),
        ("TICKET_CANCEL", "Cancelar tickets o lineas"),
        ("CASH_SHIFT_OPEN", "Abrir corte de caja"),
        ("CASH_SHIFT_CLOSE", "Cerrar corte de caja"),
        ("EXPENSE_CREATE", "Registrar gastos"),
        ("INVENTORY_ADJUST", "Ajustar inventario"),
        ("REPRINT", "Autorizar reimpresiones"),
    ]

    permissions: dict[str, Permission] = {}

    for permission_key, description in permission_defs:
        permission, _ = get_or_create(
            session,
            Permission,
            {"permission_key": permission_key},
            {"description": description, "active": True, "sync_status": "ACTIVE"},
        )
        permissions[permission_key] = permission

    role_defs = {
        "ADMIN": ["DISCOUNT_AUTHORIZE", "TICKET_CANCEL", "CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE", "INVENTORY_ADJUST", "REPRINT"],
        "GERENTE": ["DISCOUNT_AUTHORIZE", "TICKET_CANCEL", "CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE", "REPRINT"],
        "CAJERO": ["CASH_SHIFT_OPEN", "EXPENSE_CREATE"],
        "ALMACEN": ["INVENTORY_ADJUST"],
    }

    roles: dict[str, Role] = {}

    for role_key, permission_keys in role_defs.items():
        role, _ = get_or_create(
            session,
            Role,
            {"role_key": role_key},
            {"name": role_key.title(), "active": True, "sync_status": "ACTIVE"},
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
        {"employee_code": "EMP-0001"},
        {
            "full_name": "Administrador",
            "pos_alias": "Admin",
            "active": True,
            "sync_status": "ACTIVE",
        },
    )

    get_or_create(
        session,
        EmployeeRole,
        {"employee_id": admin.id, "role_id": roles["ADMIN"].id},
    )


def run_seed() -> None:
    with SessionLocal() as session:
        seed_business_settings(session)
        seed_folio_sequences(session)
        seed_payment_methods(session)
        seed_service_zones_and_tables(session)
        seed_pos_devices(session)
        seed_units(session)
        seed_categories_and_stations(session)
        seed_logical_printers(session)
        seed_development_products(session)
        seed_roles_permissions_and_admin(session)
        session.commit()


if __name__ == "__main__":
    run_seed()
    print("Seed inicial aplicado correctamente.")
