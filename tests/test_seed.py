from sqlalchemy import select

from app.db.seed import run_seed
from app.models import BusinessSetting, DiningTable, Employee, FolioSequence, PaymentMethod, Role
from app.core.database import SessionLocal


def test_seed_initial_data_is_idempotent() -> None:
    run_seed()
    run_seed()

    with SessionLocal() as session:
        business_count = len(session.execute(select(BusinessSetting)).scalars().all())
        ticket_sequence_count = len(
            session.execute(
                select(FolioSequence).where(FolioSequence.sequence_key == "TICKET")
            ).scalars().all()
        )
        cash_method_count = len(
            session.execute(
                select(PaymentMethod).where(PaymentMethod.method_key == "CASH")
            ).scalars().all()
        )
        admin_count = len(
            session.execute(
                select(Employee).where(Employee.employee_code == "EMP-0001")
            ).scalars().all()
        )
        admin_role_count = len(
            session.execute(
                select(Role).where(Role.role_key == "ADMIN")
            ).scalars().all()
        )
        table_count = len(session.execute(select(DiningTable)).scalars().all())

    assert business_count == 1
    assert ticket_sequence_count == 1
    assert cash_method_count == 1
    assert admin_count == 1
    assert admin_role_count == 1
    assert table_count >= 20
