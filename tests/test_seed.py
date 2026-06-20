from sqlalchemy import select

from app.db.seed import run_seed
from app.models import (
    BusinessSetting,
    DiningTable,
    Employee,
    FolioSequence,
    PaymentMethod,
    Product,
    ProductPackage,
    ProductPackageItem,
    Printer,
    Role,
)
from app.core.database import SessionLocal
from scripts.deactivate_demo_catalog import deactivate_demo_catalog


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
