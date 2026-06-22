import pytest
from sqlalchemy import func, select

from app.db.seed import run_seed
from app.models import (
    BusinessSetting,
    DiningTable,
    DiscountPreset,
    Employee,
    InventoryItem,
    Permission,
    FolioSequence,
    PaymentMethod,
    Product,
    ProductPackage,
    ProductPackageItem,
    Printer,
    Role,
    RolePermission,
    ProductionStation,
    ProductVariantGroup,
)
from app.core.database import SessionLocal
from scripts.deactivate_demo_catalog import deactivate_demo_catalog
from scripts.reset_seed_catalog_data import CONFIRMATION, reset_seed_catalog_data


def test_seed_initial_data_is_idempotent() -> None:
    run_seed(include_development_data=True)
    run_seed(include_development_data=True)

    with SessionLocal() as session:
        business_count = len(session.execute(select(BusinessSetting)).scalars().all())
        ticket_sequence_count = len(
            session.execute(
                select(FolioSequence).where(FolioSequence.sequence_key == "TICKET")
            )
            .scalars()
            .all()
        )
        cash_method_count = len(
            session.execute(
                select(PaymentMethod).where(PaymentMethod.method_key == "Efectivo")
            )
            .scalars()
            .all()
        )
        admin_count = len(
            session.execute(
                select(Employee).where(Employee.employee_code == "EMP-0001")
            )
            .scalars()
            .all()
        )
        admin_role_count = len(
            session.execute(select(Role).where(Role.role_key == "ADMIN"))
            .scalars()
            .all()
        )
        table_count = len(session.execute(select(DiningTable)).scalars().all())
        demo_products = (
            session.execute(
                select(Product).where(
                    Product.sku.in_(("DEV-CHELA", "DEV-SAKE", "DEV-CHELA-SAKE"))
                )
            )
            .scalars()
            .all()
        )
        package = session.execute(
            select(ProductPackage).join(Product).where(Product.sku == "DEV-CHELA-SAKE")
        ).scalar_one()
        package_item_count = len(
            session.execute(
                select(ProductPackageItem).where(
                    ProductPackageItem.package_id == package.id
                )
            )
            .scalars()
            .all()
        )
        logical_printer_count = len(
            session.execute(
                select(Printer).where(
                    Printer.printer_key.in_(
                        (
                            "CAJA",
                            "COCINA",
                            "BARRA_FRIA",
                            "COCTELERIA",
                            "BARRA_CALIENTE",
                        )
                    )
                )
            )
            .scalars()
            .all()
        )

    assert business_count == 1
    assert ticket_sequence_count == 1
    assert cash_method_count == 1
    assert admin_count == 1
    assert admin_role_count == 1
    assert table_count >= 20
    assert len(demo_products) == 3
    assert package_item_count == 2
    assert logical_printer_count == 5


def test_operational_seed_does_not_reactivate_demo_catalog() -> None:
    deactivate_demo_catalog()
    run_seed()

    with SessionLocal() as session:
        demo_products = session.scalars(
            select(Product).where(Product.sku.like("DEV-%"))
        ).all()

    assert len(demo_products) == 4
    assert all(not product.active and not product.visible_pos for product in demo_products)


def test_real_operational_seed_matches_catalog_contract() -> None:
    run_seed()
    with SessionLocal() as session:
        assert session.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.active.is_(True))) == 96
        assert session.scalar(select(func.count(Product.id)).where(Product.active.is_(True), Product.visible_pos.is_(True))) == 31
        assert session.scalar(select(func.count(DiningTable.id)).where(DiningTable.active.is_(True))) == 17
        assert set(session.scalars(select(ProductionStation.station_key).where(ProductionStation.active.is_(True)))) == {"COCINA", "BARRA"}
        assert set(session.scalars(select(DiscountPreset.preset_key))) == {
            "CORTESIA_TOTAL",
            "DESC_10",
            "DESC_50_MXN",
        }
        assert list(session.scalars(select(Employee.employee_code).where(Employee.active.is_(True)))) == ["ADMIN"]
        assert set(session.scalars(select(Role.role_key).where(Role.active.is_(True)))) >= {"ADMIN", "GERENTE", "CAJERO", "ALMACEN", "SOPORTE"}



def test_admin_permissions_and_yakitori_variants_are_reproducible() -> None:
    run_seed()
    run_seed()
    with SessionLocal() as session:
        admin_permissions = set(session.scalars(
            select(Permission.permission_key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .where(Role.role_key == "ADMIN")
        ))
        assert {"ADMIN_READ", "SUPPORT_ACCESS"} <= admin_permissions

        groups = list(
            session.scalars(
                select(ProductVariantGroup)
                .join(Product)
                .where(Product.sku.like("YAK-%"))
            )
        )
        assert len(groups) == 8
        groups_by_key = {(group.product.sku, group.name): group for group in groups}
        combo = groups_by_key[("YAK-COC-MIX", "BROCHETAS")]
        assert combo.name == "BROCHETAS"
        assert combo.required is True
        assert (combo.min_select, combo.max_select) == (3, 3)

        option_skus = {option.sku for option in combo.options}
        assert option_skus == {
            "YAK-COC-POLL",
            "YAK-COC-PORK",
            "YAK-COC-PUL",
            "YAK-COC_CAM",
            "YAK-COC-VER",
            "YAK-COC-HONG",
        }

        for sku in {
            "YAK-COC-POLL",
            "YAK-COC-PORK",
            "YAK-COC-PUL",
            "YAK-COC_CAM",
            "YAK-COC-VER",
            "YAK-COC-HONG",
        }:
            group = groups_by_key[(sku, "Preparación")]
            assert group.name == "Preparación"
            assert group.required is True
            assert (group.min_select, group.max_select) == (1, 1)
            assert [option.name for option in group.options] == ["Tempura", "Asada"]
            assert all(option.active for option in group.options)
            assert all(option.price_delta_cents == 0 for option in group.options)

        mix_preparation = groups_by_key[("YAK-COC-MIX", "Preparación")]
        assert mix_preparation.required is True
        assert (mix_preparation.min_select, mix_preparation.max_select) == (1, 1)
        assert [option.name for option in mix_preparation.options] == [
            "Tempura",
            "Asada",
        ]

def test_sqlite_catalog_reset_requires_confirmation_and_dry_run_is_read_only() -> None:
    run_seed()
    with SessionLocal() as session:
        before = reset_seed_catalog_data(session, dry_run=True)
        assert before["before"] == before["after"]
        with pytest.raises(ValueError, match=CONFIRMATION):
            reset_seed_catalog_data(session, dry_run=False, confirmation="incorrecta")
