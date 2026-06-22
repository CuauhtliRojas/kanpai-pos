import pytest
from sqlalchemy import select

from app.core.database import SessionLocal
from app.db.seed import run_seed
from app.domain.constants import PrintJobType, PrintStatus, TicketStatus
from app.models import DiningTable, Employee, PrintJob, Printer
from app.services.cash_shift_service import close_cash_shift, open_cash_shift
from app.services.exceptions import BusinessConflictError
from app.services.ticket_service import open_ticket_for_table
from scripts.reset_operational_data import reset_operational_data


@pytest.fixture(autouse=True)
def cash_data():
    run_seed(include_development_data=True)
    with SessionLocal() as db:
        reset_operational_data(db)
        db.commit()
    yield


def _context(db):
    employee = db.scalar(select(Employee).where(Employee.employee_code == "EMP-0001"))
    table = db.scalar(
        select(DiningTable)
        .where(DiningTable.active.is_(True))
        .order_by(DiningTable.sort_order)
    )
    shift = open_cash_shift(db, employee.id, 0)
    db.flush()
    return employee, table, shift


@pytest.mark.parametrize("ticket_status", [TicketStatus.OPEN, TicketStatus.IN_PAYMENT])
def test_close_blocks_with_operational_ticket_details(ticket_status):
    with SessionLocal() as db:
        employee, table, shift = _context(db)
        ticket = open_ticket_for_table(db, table.id, employee.id)
        ticket.status = ticket_status
        db.flush()

        with pytest.raises(BusinessConflictError) as error:
            close_cash_shift(db, shift.id, employee.id, 0)

        message = str(error.value)
        assert table.display_name in message
        assert ticket.folio in message
        assert ticket_status in message
        assert "Termina o cobra" in message


def test_close_allows_pending_print_jobs_and_enqueues_cash_shift_job():
    with SessionLocal() as db:
        employee, _, shift = _context(db)
        printer = db.scalar(select(Printer).where(Printer.printer_key == "CAJA"))
        db.add(
            PrintJob(
                folio="PRN-PENDING-QA",
                job_type=PrintJobType.TICKET,
                printer_id=printer.id,
                printer_key_snapshot=printer.printer_key,
                cash_shift_id=shift.id,
                content_snapshot="pendiente",
                status=PrintStatus.PENDING,
                idempotency_key="QA:PENDING:CLOSE",
            )
        )
        db.flush()

        closed = close_cash_shift(db, shift.id, employee.id, 0)
        jobs = list(
            db.scalars(select(PrintJob).where(PrintJob.cash_shift_id == shift.id))
        )

        assert closed.status == "Cerrado"
        assert {job.job_type for job in jobs} == {
            PrintJobType.TICKET,
            PrintJobType.CASH_SHIFT,
        }
