from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BusinessSetting(TimestampMixin, Base):
    __tablename__ = "business_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_name: Mapped[str] = mapped_column(String(160), default="Kanpai", nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="MXN", nullable=False)
    ticket_message: Mapped[Optional[str]] = mapped_column(Text)
    logo_path: Mapped[Optional[str]] = mapped_column(String(500))
    inventory_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timezone: Mapped[str] = mapped_column(String(80), default="America/Mexico_City", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FolioSequence(TimestampMixin, Base):
    __tablename__ = "folio_sequences"
    __table_args__ = (
        UniqueConstraint("sequence_key", name="uq_folio_sequence_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sequence_key: Mapped[str] = mapped_column(String(64), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    next_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    padding: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PosDevice(TimestampMixin, Base):
    __tablename__ = "pos_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_name: Mapped[str] = mapped_column(String(120), nullable=False)
    location_label: Mapped[Optional[str]] = mapped_column(String(120))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sessions: Mapped[list["PosSession"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )


class PosSession(TimestampMixin, Base):
    __tablename__ = "pos_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    device_id: Mapped[int] = mapped_column(ForeignKey("pos_devices.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    device: Mapped["PosDevice"] = relationship(back_populates="sessions")


class ServiceZone(TimestampMixin, Base):
    __tablename__ = "service_zones"
    __table_args__ = (
        UniqueConstraint("zone_key", name="uq_service_zone_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tables: Mapped[list["DiningTable"]] = relationship(
        back_populates="zone",
        cascade="all, delete-orphan",
    )


class DiningTable(TimestampMixin, Base):
    __tablename__ = "dining_tables"
    __table_args__ = (
        UniqueConstraint("table_code", name="uq_dining_table_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_code: Mapped[str] = mapped_column(String(40), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    zone_id: Mapped[int] = mapped_column(ForeignKey("service_zones.id"), nullable=False)
    buzzer_number: Mapped[Optional[int]] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status_cache: Mapped[str] = mapped_column(String(32), default="FREE", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    zone: Mapped["ServiceZone"] = relationship(back_populates="tables")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="table")


class TableStatusEvent(Base):
    __tablename__ = "table_status_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("dining_tables.id"), nullable=False)
    ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tickets.id"))
    actor_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    from_status: Mapped[Optional[str]] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CashShift(TimestampMixin, Base):
    __tablename__ = "cash_shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    opened_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    closed_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    opening_cash_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    declared_cash_cents: Mapped[Optional[int]] = mapped_column(Integer)
    expected_cash_cents: Mapped[Optional[int]] = mapped_column(Integer)
    cash_difference_cents: Mapped[Optional[int]] = mapped_column(Integer)
    closing_note: Mapped[Optional[str]] = mapped_column(Text)
    sales_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cash_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    card_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    transfer_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expenses_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    net_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ticket_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_ticket_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="cash_shift")
    payments: Mapped[list["Payment"]] = relationship(back_populates="cash_shift")
    expenses: Mapped[list["CashExpense"]] = relationship(back_populates="cash_shift")


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    cash_shift_id: Mapped[int] = mapped_column(ForeignKey("cash_shifts.id"), nullable=False)
    table_id: Mapped[int] = mapped_column(ForeignKey("dining_tables.id"), nullable=False)
    opened_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    waiter_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    closed_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    cancelled_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    guest_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), default="UNPAID", nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    billing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    inventory_consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    subtotal_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tax_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    cash_shift: Mapped["CashShift"] = relationship(back_populates="tickets")
    table: Mapped["DiningTable"] = relationship(back_populates="tickets")
    lines: Mapped[list["TicketLine"]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
        foreign_keys="TicketLine.ticket_id",
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="ticket")
    discounts: Mapped[list["TicketDiscount"]] = relationship(back_populates="ticket")


class TicketLine(TimestampMixin, Base):
    __tablename__ = "ticket_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    parent_ticket_line_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_lines.id"))
    package_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_packages.id"))
    package_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_package_items.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    line_type: Mapped[str] = mapped_column(String(32), default="SIMPLE", nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    line_total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_mode: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(220), nullable=False)
    product_sku_snapshot: Mapped[Optional[str]] = mapped_column(String(80))
    category_id_snapshot: Mapped[Optional[int]] = mapped_column(Integer)
    station_id_snapshot: Mapped[Optional[int]] = mapped_column(Integer)
    note: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="CAPTURED", nullable=False)
    round_number: Mapped[Optional[int]] = mapped_column(Integer)
    created_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    cancelled_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    cancel_authorized_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    ticket: Mapped["Ticket"] = relationship(
        back_populates="lines",
        foreign_keys=[ticket_id],
    )
    parent_line: Mapped[Optional["TicketLine"]] = relationship(
        remote_side=[id],
        foreign_keys=[parent_ticket_line_id],
    )
    notes: Mapped[list["TicketLineNote"]] = relationship(
        back_populates="ticket_line",
        cascade="all, delete-orphan",
    )


class TicketLineNote(Base):
    __tablename__ = "ticket_line_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_line_id: Mapped[int] = mapped_column(ForeignKey("ticket_lines.id"), nullable=False)
    note_type: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ticket_line: Mapped["TicketLine"] = relationship(back_populates="notes")


class TicketDiscount(Base):
    __tablename__ = "ticket_discounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    promotion_id: Mapped[Optional[int]] = mapped_column(Integer)
    discount_source: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    authorized_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    created_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    ticket: Mapped["Ticket"] = relationship(back_populates="discounts")


class PaymentMethod(TimestampMixin, Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        UniqueConstraint("method_key", name="uq_payment_method_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    method_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    requires_reference: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    cash_shift_id: Mapped[int] = mapped_column(ForeignKey("cash_shifts.id"), nullable=False)
    payment_method_id: Mapped[int] = mapped_column(ForeignKey("payment_methods.id"), nullable=False)
    cashier_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    received_cents: Mapped[Optional[int]] = mapped_column(Integer)
    change_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    cancelled_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    ticket: Mapped["Ticket"] = relationship(back_populates="payments")
    cash_shift: Mapped["CashShift"] = relationship(back_populates="payments")
    payment_method: Mapped["PaymentMethod"] = relationship()


class CommandBatch(Base):
    __tablename__ = "command_batches"
    __table_args__ = (
        UniqueConstraint("ticket_id", "round_number", "batch_type", name="uq_command_batch_round_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_type: Mapped[str] = mapped_column(String(32), default="ORDER", nullable=False)
    created_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    station_orders: Mapped[list["StationOrder"]] = relationship(
        back_populates="command_batch",
        cascade="all, delete-orphan",
    )


class StationOrder(Base):
    __tablename__ = "station_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    command_batch_id: Mapped[int] = mapped_column(ForeignKey("command_batches.id"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("production_stations.id"), nullable=False)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", nullable=False)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    command_batch: Mapped["CommandBatch"] = relationship(back_populates="station_orders")
    lines: Mapped[list["StationOrderLine"]] = relationship(
        back_populates="station_order",
        cascade="all, delete-orphan",
    )


class StationOrderLine(Base):
    __tablename__ = "station_order_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_order_id: Mapped[int] = mapped_column(ForeignKey("station_orders.id"), nullable=False)
    ticket_line_id: Mapped[int] = mapped_column(ForeignKey("ticket_lines.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    product_name_snapshot: Mapped[str] = mapped_column(String(220), nullable=False)
    note_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    line_action: Mapped[str] = mapped_column(String(32), default="ADD", nullable=False)

    station_order: Mapped["StationOrder"] = relationship(back_populates="lines")


class Printer(TimestampMixin, Base):
    __tablename__ = "printers"
    __table_args__ = (
        UniqueConstraint("printer_key", name="uq_printer_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    printer_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    station_id: Mapped[Optional[int]] = mapped_column(ForeignKey("production_stations.id"))
    paper_width_mm: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    connection_type: Mapped[str] = mapped_column(String(32), default="USB", nullable=False)
    connection_ref: Mapped[Optional[str]] = mapped_column(String(255))
    autocut_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PrintJob(TimestampMixin, Base):
    __tablename__ = "print_jobs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_print_job_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id"), nullable=False)
    printer_key_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tickets.id"))
    cash_shift_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cash_shifts.id"))
    station_order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("station_orders.id"))
    command_batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("command_batches.id"))
    content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    claimed_by: Mapped[Optional[str]] = mapped_column(String(160))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    printer: Mapped["Printer"] = relationship()


class CashExpense(TimestampMixin, Base):
    __tablename__ = "cash_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    cash_shift_id: Mapped[int] = mapped_column(ForeignKey("cash_shifts.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(32))
    payment_method_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payment_methods.id"))
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    registered_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    authorized_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    note: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    cash_shift: Mapped["CashShift"] = relationship(back_populates="expenses")
    payment_method: Mapped["PaymentMethod"] = relationship()


class Authorization(Base):
    __tablename__ = "authorizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    authorization_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    requested_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    authorized_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="APPROVED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
    cash_shift_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cash_shifts.id"))
    ticket_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tickets.id"))
    before_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    after_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
