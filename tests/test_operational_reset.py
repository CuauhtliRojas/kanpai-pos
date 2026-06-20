from itertools import count

import pytest
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.models import (
    CashShift,
    DiningTable,
    Employee,
    Payment,
    PaymentMethod,
    Printer,
    PrintJob,
    Product,
    Ticket,
)
from scripts.reset_operational_data import main, reset_operational_data

sequence = count(1)


@pytest.fixture(autouse=True)
def clean_reset_data() -> None:
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
    yield
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()


def _create_operations() -> None:
    with SessionLocal() as db:
        employee = db.scalar(
            select(Employee).where(Employee.employee_code == "EMP-0001")
        )
        table = db.scalar(select(DiningTable).where(DiningTable.active.is_(True)))
        method = db.scalar(
            select(PaymentMethod).where(PaymentMethod.method_key == "Efectivo")
        )
        printer = db.scalar(select(Printer).where(Printer.printer_key == "CAJA"))
        assert employee and table and method and printer
        number = next(sequence)
        shift = CashShift(
            folio=f"QA-RESET-SHIFT-{number}",
            opened_by_employee_id=employee.id,
            opening_cash_cents=0,
        )
        db.add(shift)
        db.flush()
        ticket = Ticket(
            folio=f"QA-RESET-TICKET-{number}",
            cash_shift_id=shift.id,
            table_id=table.id,
            opened_by_employee_id=employee.id,
            total_cents=100,
        )
        db.add(ticket)
        db.flush()
        db.add(
            Payment(
                folio=f"QA-RESET-PAYMENT-{number}",
                ticket_id=ticket.id,
                cash_shift_id=shift.id,
                payment_method_id=method.id,
                cashier_employee_id=employee.id,
                amount_cents=100,
            )
        )
        db.add(
            PrintJob(
                folio=f"QA-RESET-PRINT-{number}",
                job_type="Ticket",
                printer_id=printer.id,
                printer_key_snapshot=printer.printer_key,
                ticket_id=ticket.id,
                cash_shift_id=shift.id,
                content_snapshot="QA",
                idempotency_key=f"QA-RESET:{number}",
            )
        )
        table.status_cache = "Ocupada"
        db.commit()


def test_reset_deletes_operational_records() -> None:
    _create_operations()
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
        assert db.scalar(select(func.count(Ticket.id))) == 0
        assert db.scalar(select(func.count(CashShift.id))) == 0
        assert db.scalar(select(func.count(Payment.id))) == 0
        assert db.scalar(select(func.count(PrintJob.id))) == 0


def test_reset_leaves_catalogs_intact() -> None:
    _create_operations()
    with SessionLocal() as db:
        catalog_counts = {
            "products": db.scalar(select(func.count(Product.id))),
            "employees": db.scalar(select(func.count(Employee.id))),
            "methods": db.scalar(select(func.count(PaymentMethod.id))),
            "printers": db.scalar(select(func.count(Printer.id))),
        }
        reset_operational_data(db)
        db.commit()
        assert db.scalar(select(func.count(Product.id))) == catalog_counts["products"]
        assert db.scalar(select(func.count(Employee.id))) == catalog_counts["employees"]
        assert (
            db.scalar(select(func.count(PaymentMethod.id))) == catalog_counts["methods"]
        )
        assert db.scalar(select(func.count(Printer.id))) == catalog_counts["printers"]


def test_reset_returns_all_tables_to_free() -> None:
    _create_operations()
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
        assert set(db.scalars(select(DiningTable.status_cache))) == {"Libre"}


def test_reset_is_idempotent() -> None:
    with SessionLocal() as db:
        first = reset_operational_data(db)
        second = reset_operational_data(db)
        db.commit()
    assert sum(first.values()) == 0
    assert sum(second.values()) == 0


def test_reset_without_yes_does_not_delete_data(
    capsys: pytest.CaptureFixture[str],
) -> None:
    _create_operations()
    assert main([]) == 0
    assert "no data was deleted" in capsys.readouterr().out
    with SessionLocal() as db:
        assert db.scalar(select(func.count(Ticket.id))) == 1
        assert db.scalar(select(func.count(CashShift.id))) == 1
