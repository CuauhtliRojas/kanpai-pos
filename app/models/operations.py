from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.domain.database_contract import db_column
from app.domain.constants import (
    ActiveStatus,
    AuthorizationStatus,
    CommandValue,
    ConnectionType,
    PriceMode,
    ProductionOrderStatus,
    SyncStatus,
    TableStatus,
    TicketLineStatus,
    TicketLineType,
    TicketPaymentStatus,
    TicketStatus,
)


class TimestampMixin:
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = db_column(
        "updated_at",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BusinessSetting(TimestampMixin, Base):
    __tablename__ = "configuracion_negocio"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    business_name: Mapped[str] = db_column(
        "business_name", String(160), default="Kanpai", nullable=False
    )
    currency: Mapped[str] = db_column(
        "currency", String(8), default="MXN", nullable=False
    )
    ticket_message: Mapped[Optional[str]] = db_column("ticket_message", Text)
    logo_path: Mapped[Optional[str]] = db_column("logo_path", String(500))
    inventory_enabled: Mapped[bool] = db_column(
        "inventory_enabled", Boolean, default=True, nullable=False
    )
    timezone: Mapped[str] = db_column(
        "timezone", String(80), default="America/Mexico_City", nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)
    tax_enabled: Mapped[bool] = db_column(
        "tax_enabled", Boolean, default=True, nullable=False
    )
    tax_rate_bps: Mapped[int] = db_column(
        "tax_rate_bps", Integer, default=1600, nullable=False
    )
    tax_included: Mapped[bool] = db_column(
        "tax_included", Boolean, default=False, nullable=False
    )
    tax_label: Mapped[str] = db_column(
        "tax_label", String(40), default="IVA", nullable=False
    )


class FolioSequence(TimestampMixin, Base):
    __tablename__ = "secuencias_folio"
    __table_args__ = (UniqueConstraint("sequence_key", name="uq_folio_sequence_key"),)

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    sequence_key: Mapped[str] = db_column("sequence_key", String(64), nullable=False)
    prefix: Mapped[str] = db_column("prefix", String(16), nullable=False)
    next_number: Mapped[int] = db_column(
        "next_number", Integer, default=1, nullable=False
    )
    padding: Mapped[int] = db_column("padding", Integer, default=6, nullable=False)
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)


class PosDevice(TimestampMixin, Base):
    __tablename__ = "dispositivos_pos"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    device_name: Mapped[str] = db_column("device_name", String(120), nullable=False)
    location_label: Mapped[Optional[str]] = db_column("location_label", String(120))
    is_primary: Mapped[bool] = db_column(
        "is_primary", Boolean, default=False, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    sessions: Mapped[list["PosSession"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
    )


class PosSession(TimestampMixin, Base):
    __tablename__ = "sesiones_pos"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    employee_id: Mapped[int] = db_column(
        "employee_id", ForeignKey("empleados.id"), nullable=False
    )
    device_id: Mapped[int] = db_column(
        "device_id", ForeignKey("dispositivos_pos.id"), nullable=False
    )
    status: Mapped[str] = db_column(
        "status", String(32), default=TicketStatus.OPEN, nullable=False
    )
    opened_at: Mapped[datetime] = db_column(
        "opened_at", DateTime, default=datetime.utcnow, nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = db_column("closed_at", DateTime)

    device: Mapped["PosDevice"] = relationship(back_populates="sessions")


class ServiceZone(TimestampMixin, Base):
    __tablename__ = "zonas_servicio"
    __table_args__ = (UniqueConstraint("zone_key", name="uq_service_zone_key"),)

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    zone_key: Mapped[str] = db_column("zone_key", String(64), nullable=False)
    name: Mapped[str] = db_column("name", String(120), nullable=False)
    sort_order: Mapped[int] = db_column(
        "sort_order", Integer, default=0, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    tables: Mapped[list["DiningTable"]] = relationship(
        back_populates="zone",
        cascade="all, delete-orphan",
    )


class DiningTable(TimestampMixin, Base):
    __tablename__ = "mesas"
    __table_args__ = (UniqueConstraint("table_code", name="uq_dining_table_code"),)

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    table_code: Mapped[str] = db_column("table_code", String(40), nullable=False)
    display_name: Mapped[str] = db_column("display_name", String(120), nullable=False)
    zone_id: Mapped[int] = db_column(
        "zone_id", ForeignKey("zonas_servicio.id"), nullable=False
    )
    buzzer_number: Mapped[Optional[int]] = db_column("buzzer_number", Integer)
    sort_order: Mapped[int] = db_column(
        "sort_order", Integer, default=0, nullable=False
    )
    status_cache: Mapped[str] = db_column(
        "status_cache", String(32), default=TableStatus.FREE, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    zone: Mapped["ServiceZone"] = relationship(back_populates="tables")
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="table")


class TableStatusEvent(Base):
    __tablename__ = "eventos_estado_mesa"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    table_id: Mapped[int] = db_column(
        "table_id", ForeignKey("mesas.id"), nullable=False
    )
    ticket_id: Mapped[Optional[int]] = db_column("ticket_id", ForeignKey("tickets.id"))
    actor_employee_id: Mapped[Optional[int]] = db_column(
        "actor_employee_id", ForeignKey("empleados.id")
    )
    from_status: Mapped[Optional[str]] = db_column("from_status", String(32))
    to_status: Mapped[str] = db_column("to_status", String(32), nullable=False)
    reason: Mapped[Optional[str]] = db_column("reason", Text)
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )


class CashShift(TimestampMixin, Base):
    __tablename__ = "cortes_caja"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    status: Mapped[str] = db_column(
        "status", String(32), default=TicketStatus.OPEN, nullable=False
    )
    opened_by_employee_id: Mapped[int] = db_column(
        "opened_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    closed_by_employee_id: Mapped[Optional[int]] = db_column(
        "closed_by_employee_id", ForeignKey("empleados.id")
    )
    opened_at: Mapped[datetime] = db_column(
        "opened_at", DateTime, default=datetime.utcnow, nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = db_column("closed_at", DateTime)
    opening_cash_cents: Mapped[int] = db_column(
        "opening_cash_cents", Integer, default=0, nullable=False
    )
    declared_cash_cents: Mapped[Optional[int]] = db_column(
        "declared_cash_cents", Integer
    )
    expected_cash_cents: Mapped[Optional[int]] = db_column(
        "expected_cash_cents", Integer
    )
    cash_difference_cents: Mapped[Optional[int]] = db_column(
        "cash_difference_cents", Integer
    )
    closing_note: Mapped[Optional[str]] = db_column("closing_note", Text)
    sales_total_cents: Mapped[int] = db_column(
        "sales_total_cents", Integer, default=0, nullable=False
    )
    cash_total_cents: Mapped[int] = db_column(
        "cash_total_cents", Integer, default=0, nullable=False
    )
    card_total_cents: Mapped[int] = db_column(
        "card_total_cents", Integer, default=0, nullable=False
    )
    transfer_total_cents: Mapped[int] = db_column(
        "transfer_total_cents", Integer, default=0, nullable=False
    )
    expenses_total_cents: Mapped[int] = db_column(
        "expenses_total_cents", Integer, default=0, nullable=False
    )
    net_total_cents: Mapped[int] = db_column(
        "net_total_cents", Integer, default=0, nullable=False
    )
    ticket_count: Mapped[int] = db_column(
        "ticket_count", Integer, default=0, nullable=False
    )
    average_ticket_cents: Mapped[int] = db_column(
        "average_ticket_cents", Integer, default=0, nullable=False
    )
    notes: Mapped[Optional[str]] = db_column("notes", Text)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="cash_shift")
    payments: Mapped[list["Payment"]] = relationship(back_populates="cash_shift")
    expenses: Mapped[list["CashExpense"]] = relationship(back_populates="cash_shift")


class Ticket(TimestampMixin, Base):
    __tablename__ = "tickets"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    cash_shift_id: Mapped[int] = db_column(
        "cash_shift_id", ForeignKey("cortes_caja.id"), nullable=False
    )
    table_id: Mapped[int] = db_column(
        "table_id", ForeignKey("mesas.id"), nullable=False
    )
    opened_by_employee_id: Mapped[int] = db_column(
        "opened_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    waiter_employee_id: Mapped[Optional[int]] = db_column(
        "waiter_employee_id", ForeignKey("empleados.id")
    )
    closed_by_employee_id: Mapped[Optional[int]] = db_column(
        "closed_by_employee_id", ForeignKey("empleados.id")
    )
    cancelled_by_employee_id: Mapped[Optional[int]] = db_column(
        "cancelled_by_employee_id", ForeignKey("empleados.id")
    )
    guest_count: Mapped[int] = db_column(
        "guest_count", Integer, default=1, nullable=False
    )
    status: Mapped[str] = db_column(
        "status", String(32), default=TicketStatus.OPEN, nullable=False
    )
    payment_status: Mapped[str] = db_column(
        "payment_status", String(32), default=TicketPaymentStatus.UNPAID, nullable=False
    )
    note: Mapped[Optional[str]] = db_column("note", Text)
    opened_at: Mapped[datetime] = db_column(
        "opened_at", DateTime, default=datetime.utcnow, nullable=False
    )
    billing_started_at: Mapped[Optional[datetime]] = db_column(
        "billing_started_at", DateTime
    )
    paid_at: Mapped[Optional[datetime]] = db_column("paid_at", DateTime)
    inventory_consumed_at: Mapped[Optional[datetime]] = db_column(
        "inventory_consumed_at", DateTime
    )
    cancelled_at: Mapped[Optional[datetime]] = db_column("cancelled_at", DateTime)
    cancel_reason: Mapped[Optional[str]] = db_column("cancel_reason", Text)
    subtotal_cents: Mapped[int] = db_column(
        "subtotal_cents", Integer, default=0, nullable=False
    )
    discount_cents: Mapped[int] = db_column(
        "discount_cents", Integer, default=0, nullable=False
    )
    tax_cents: Mapped[int] = db_column("tax_cents", Integer, default=0, nullable=False)
    total_cents: Mapped[int] = db_column(
        "total_cents", Integer, default=0, nullable=False
    )

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
    __tablename__ = "lineas_ticket"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    ticket_id: Mapped[int] = db_column(
        "ticket_id", ForeignKey("tickets.id"), nullable=False
    )
    parent_ticket_line_id: Mapped[Optional[int]] = db_column(
        "parent_ticket_line_id", ForeignKey("lineas_ticket.id")
    )
    package_id: Mapped[Optional[int]] = db_column(
        "package_id", ForeignKey("paquetes_producto.id")
    )
    package_item_id: Mapped[Optional[int]] = db_column(
        "package_item_id", ForeignKey("componentes_paquete_producto.id")
    )
    product_id: Mapped[int] = db_column(
        "product_id", ForeignKey("productos.id"), nullable=False
    )
    line_type: Mapped[str] = db_column(
        "line_type", String(32), default=TicketLineType.SIMPLE, nullable=False
    )
    quantity: Mapped[int] = db_column("quantity", Integer, default=1, nullable=False)
    unit_price_cents: Mapped[int] = db_column(
        "unit_price_cents", Integer, default=0, nullable=False
    )
    line_total_cents: Mapped[int] = db_column(
        "line_total_cents", Integer, default=0, nullable=False
    )
    price_mode: Mapped[str] = db_column(
        "price_mode", String(32), default=PriceMode.NORMAL, nullable=False
    )
    product_name_snapshot: Mapped[str] = db_column(
        "product_name_snapshot", String(220), nullable=False
    )
    product_sku_snapshot: Mapped[Optional[str]] = db_column(
        "product_sku_snapshot", String(80)
    )
    category_id_snapshot: Mapped[Optional[int]] = db_column(
        "category_id_snapshot", Integer
    )
    station_id_snapshot: Mapped[Optional[int]] = db_column(
        "station_id_snapshot", Integer
    )
    note: Mapped[Optional[str]] = db_column("note", Text)
    status: Mapped[str] = db_column(
        "status", String(32), default=TicketLineStatus.CAPTURED, nullable=False
    )
    round_number: Mapped[Optional[int]] = db_column("round_number", Integer)
    created_by_employee_id: Mapped[int] = db_column(
        "created_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    cancelled_by_employee_id: Mapped[Optional[int]] = db_column(
        "cancelled_by_employee_id", ForeignKey("empleados.id")
    )
    cancel_authorized_by_employee_id: Mapped[Optional[int]] = db_column(
        "cancel_authorized_by_employee_id", ForeignKey("empleados.id")
    )
    cancel_reason: Mapped[Optional[str]] = db_column("cancel_reason", Text)
    sent_at: Mapped[Optional[datetime]] = db_column("sent_at", DateTime)
    cancelled_at: Mapped[Optional[datetime]] = db_column("cancelled_at", DateTime)

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
    __tablename__ = "notas_linea_ticket"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    ticket_line_id: Mapped[int] = db_column(
        "ticket_line_id", ForeignKey("lineas_ticket.id"), nullable=False
    )
    note_type: Mapped[str] = db_column("note_type", String(32), nullable=False)
    note: Mapped[str] = db_column("note", Text, nullable=False)
    created_by_employee_id: Mapped[int] = db_column(
        "created_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )

    ticket_line: Mapped["TicketLine"] = relationship(back_populates="notes")


class TicketLineModification(Base):
    __tablename__ = "modificaciones_linea_ticket"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    ticket_line_id: Mapped[int] = db_column(
        "ticket_line_id", ForeignKey("lineas_ticket.id"), nullable=False
    )
    ticket_id: Mapped[int] = db_column(
        "ticket_id", ForeignKey("tickets.id"), nullable=False
    )
    note: Mapped[str] = db_column("note", Text, nullable=False)
    created_by_employee_id: Mapped[int] = db_column(
        "created_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )
    print_job_id: Mapped[Optional[int]] = db_column(
        "print_job_id", ForeignKey("trabajos_impresion.id")
    )


class TicketDiscount(Base):
    __tablename__ = "descuentos_ticket"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    ticket_id: Mapped[int] = db_column(
        "ticket_id", ForeignKey("tickets.id"), nullable=False
    )
    promotion_id: Mapped[Optional[int]] = db_column("promotion_id", Integer)
    discount_source: Mapped[str] = db_column(
        "discount_source", String(32), nullable=False
    )
    percent_bps: Mapped[Optional[int]] = db_column("percent_bps", Integer)
    is_courtesy: Mapped[bool] = db_column(
        "is_courtesy", Boolean, default=False, nullable=False
    )
    amount_cents: Mapped[int] = db_column(
        "amount_cents", Integer, default=0, nullable=False
    )
    reason: Mapped[Optional[str]] = db_column("reason", Text)
    authorized_by_employee_id: Mapped[Optional[int]] = db_column(
        "authorized_by_employee_id", ForeignKey("empleados.id")
    )
    created_by_employee_id: Mapped[int] = db_column(
        "created_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="discounts")


class PaymentMethod(TimestampMixin, Base):
    __tablename__ = "metodos_pago"
    __table_args__ = (UniqueConstraint("method_key", name="uq_payment_method_key"),)

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    method_key: Mapped[str] = db_column("method_key", String(64), nullable=False)
    name: Mapped[str] = db_column("name", String(120), nullable=False)
    requires_reference: Mapped[bool] = db_column(
        "requires_reference", Boolean, default=False, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)


class Payment(TimestampMixin, Base):
    __tablename__ = "pagos"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    ticket_id: Mapped[int] = db_column(
        "ticket_id", ForeignKey("tickets.id"), nullable=False
    )
    cash_shift_id: Mapped[int] = db_column(
        "cash_shift_id", ForeignKey("cortes_caja.id"), nullable=False
    )
    payment_method_id: Mapped[int] = db_column(
        "payment_method_id", ForeignKey("metodos_pago.id"), nullable=False
    )
    cashier_employee_id: Mapped[int] = db_column(
        "cashier_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    amount_cents: Mapped[int] = db_column("amount_cents", Integer, nullable=False)
    received_cents: Mapped[Optional[int]] = db_column("received_cents", Integer)
    change_cents: Mapped[int] = db_column(
        "change_cents", Integer, default=0, nullable=False
    )
    reference: Mapped[Optional[str]] = db_column("reference", String(255))
    status: Mapped[str] = db_column(
        "status", String(32), default=ActiveStatus.ACTIVE, nullable=False
    )
    cancelled_by_employee_id: Mapped[Optional[int]] = db_column(
        "cancelled_by_employee_id", ForeignKey("empleados.id")
    )
    cancel_reason: Mapped[Optional[str]] = db_column("cancel_reason", Text)
    cancelled_at: Mapped[Optional[datetime]] = db_column("cancelled_at", DateTime)

    ticket: Mapped["Ticket"] = relationship(back_populates="payments")
    cash_shift: Mapped["CashShift"] = relationship(back_populates="payments")
    payment_method: Mapped["PaymentMethod"] = relationship()


class CommandBatch(Base):
    __tablename__ = "lotes_comanda"
    __table_args__ = (
        UniqueConstraint(
            "ticket_id",
            "round_number",
            "batch_type",
            name="uq_command_batch_round_type",
        ),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    ticket_id: Mapped[int] = db_column(
        "ticket_id", ForeignKey("tickets.id"), nullable=False
    )
    round_number: Mapped[int] = db_column("round_number", Integer, nullable=False)
    batch_type: Mapped[str] = db_column(
        "batch_type", String(32), default=CommandValue.ORDER, nullable=False
    )
    created_by_employee_id: Mapped[int] = db_column(
        "created_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )

    station_orders: Mapped[list["StationOrder"]] = relationship(
        back_populates="command_batch",
        cascade="all, delete-orphan",
    )


class StationOrder(Base):
    __tablename__ = "ordenes_estacion"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    command_batch_id: Mapped[int] = db_column(
        "command_batch_id", ForeignKey("lotes_comanda.id"), nullable=False
    )
    ticket_id: Mapped[int] = db_column(
        "ticket_id", ForeignKey("tickets.id"), nullable=False
    )
    station_id: Mapped[int] = db_column(
        "station_id", ForeignKey("estaciones_produccion.id"), nullable=False
    )
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    status: Mapped[str] = db_column(
        "status", String(32), default=ProductionOrderStatus.QUEUED, nullable=False
    )
    received_at: Mapped[Optional[datetime]] = db_column("received_at", DateTime)
    started_at: Mapped[Optional[datetime]] = db_column("started_at", DateTime)
    completed_at: Mapped[Optional[datetime]] = db_column("completed_at", DateTime)
    delivered_at: Mapped[Optional[datetime]] = db_column("delivered_at", DateTime)
    received_by_employee_id: Mapped[Optional[int]] = db_column(
        "received_by_employee_id", ForeignKey("empleados.id")
    )
    started_by_employee_id: Mapped[Optional[int]] = db_column(
        "started_by_employee_id", ForeignKey("empleados.id")
    )
    completed_by_employee_id: Mapped[Optional[int]] = db_column(
        "completed_by_employee_id", ForeignKey("empleados.id")
    )
    delivered_by_employee_id: Mapped[Optional[int]] = db_column(
        "delivered_by_employee_id", ForeignKey("empleados.id")
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )

    command_batch: Mapped["CommandBatch"] = relationship(
        back_populates="station_orders"
    )
    lines: Mapped[list["StationOrderLine"]] = relationship(
        back_populates="station_order",
        cascade="all, delete-orphan",
    )


class StationOrderLine(Base):
    __tablename__ = "lineas_orden_estacion"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    station_order_id: Mapped[int] = db_column(
        "station_order_id", ForeignKey("ordenes_estacion.id"), nullable=False
    )
    ticket_line_id: Mapped[int] = db_column(
        "ticket_line_id", ForeignKey("lineas_ticket.id"), nullable=False
    )
    quantity: Mapped[int] = db_column("quantity", Integer, default=1, nullable=False)
    product_name_snapshot: Mapped[str] = db_column(
        "product_name_snapshot", String(220), nullable=False
    )
    note_snapshot: Mapped[Optional[str]] = db_column("note_snapshot", Text)
    line_action: Mapped[str] = db_column(
        "line_action", String(32), default=CommandValue.ADD, nullable=False
    )

    station_order: Mapped["StationOrder"] = relationship(back_populates="lines")


class Printer(TimestampMixin, Base):
    __tablename__ = "impresoras"
    __table_args__ = (UniqueConstraint("printer_key", name="uq_printer_key"),)

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    printer_key: Mapped[str] = db_column("printer_key", String(64), nullable=False)
    name: Mapped[str] = db_column("name", String(120), nullable=False)
    station_id: Mapped[Optional[int]] = db_column(
        "station_id", ForeignKey("estaciones_produccion.id")
    )
    paper_width_mm: Mapped[int] = db_column(
        "paper_width_mm", Integer, default=80, nullable=False
    )
    connection_type: Mapped[str] = db_column(
        "connection_type", String(32), default=ConnectionType.USB, nullable=False
    )
    connection_ref: Mapped[Optional[str]] = db_column("connection_ref", String(255))
    autocut_enabled: Mapped[bool] = db_column(
        "autocut_enabled", Boolean, default=True, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)


class PrintJob(TimestampMixin, Base):
    __tablename__ = "trabajos_impresion"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_print_job_idempotency_key"),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    job_type: Mapped[str] = db_column("job_type", String(64), nullable=False)
    printer_id: Mapped[int] = db_column(
        "printer_id", ForeignKey("impresoras.id"), nullable=False
    )
    printer_key_snapshot: Mapped[str] = db_column(
        "printer_key_snapshot", String(64), nullable=False
    )
    ticket_id: Mapped[Optional[int]] = db_column("ticket_id", ForeignKey("tickets.id"))
    cash_shift_id: Mapped[Optional[int]] = db_column(
        "cash_shift_id", ForeignKey("cortes_caja.id")
    )
    station_order_id: Mapped[Optional[int]] = db_column(
        "station_order_id", ForeignKey("ordenes_estacion.id")
    )
    command_batch_id: Mapped[Optional[int]] = db_column(
        "command_batch_id", ForeignKey("lotes_comanda.id")
    )
    content_snapshot: Mapped[str] = db_column("content_snapshot", Text, nullable=False)
    status: Mapped[str] = db_column(
        "status", String(32), default=SyncStatus.PENDING, nullable=False
    )
    attempts: Mapped[int] = db_column("attempts", Integer, default=0, nullable=False)
    claimed_at: Mapped[Optional[datetime]] = db_column("claimed_at", DateTime)
    claimed_by: Mapped[Optional[str]] = db_column("claimed_by", String(160))
    last_error: Mapped[Optional[str]] = db_column("last_error", Text)
    idempotency_key: Mapped[str] = db_column(
        "idempotency_key", String(160), nullable=False
    )
    printed_at: Mapped[Optional[datetime]] = db_column("printed_at", DateTime)
    failed_at: Mapped[Optional[datetime]] = db_column("failed_at", DateTime)
    next_retry_at: Mapped[Optional[datetime]] = db_column("next_retry_at", DateTime)

    printer: Mapped["Printer"] = relationship()


class CashExpense(TimestampMixin, Base):
    __tablename__ = "gastos_caja"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    cash_shift_id: Mapped[int] = db_column(
        "cash_shift_id", ForeignKey("cortes_caja.id"), nullable=False
    )
    description: Mapped[str] = db_column("description", String(255), nullable=False)
    category: Mapped[Optional[str]] = db_column("category", String(32))
    payment_method_id: Mapped[Optional[int]] = db_column(
        "payment_method_id", ForeignKey("metodos_pago.id")
    )
    amount_cents: Mapped[int] = db_column("amount_cents", Integer, nullable=False)
    registered_by_employee_id: Mapped[int] = db_column(
        "registered_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    authorized_by_employee_id: Mapped[Optional[int]] = db_column(
        "authorized_by_employee_id", ForeignKey("empleados.id")
    )
    note: Mapped[Optional[str]] = db_column("note", Text)
    status: Mapped[str] = db_column(
        "status", String(32), default=ActiveStatus.ACTIVE, nullable=False
    )

    cash_shift: Mapped["CashShift"] = relationship(back_populates="expenses")
    payment_method: Mapped["PaymentMethod"] = relationship()


class Authorization(Base):
    __tablename__ = "autorizaciones"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    authorization_type: Mapped[str] = db_column(
        "authorization_type", String(64), nullable=False
    )
    target_entity: Mapped[str] = db_column("target_entity", String(80), nullable=False)
    target_id: Mapped[int] = db_column("target_id", Integer, nullable=False)
    requested_by_employee_id: Mapped[int] = db_column(
        "requested_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    authorized_by_employee_id: Mapped[int] = db_column(
        "authorized_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    reason: Mapped[Optional[str]] = db_column("reason", Text)
    status: Mapped[str] = db_column(
        "status", String(32), default=AuthorizationStatus.APPROVED, nullable=False
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )


class AuditEvent(Base):
    __tablename__ = "eventos_auditoria"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    event_type: Mapped[str] = db_column("event_type", String(120), nullable=False)
    entity_type: Mapped[str] = db_column("entity_type", String(80), nullable=False)
    entity_id: Mapped[int] = db_column("entity_id", Integer, nullable=False)
    actor_employee_id: Mapped[Optional[int]] = db_column(
        "actor_employee_id", ForeignKey("empleados.id")
    )
    cash_shift_id: Mapped[Optional[int]] = db_column(
        "cash_shift_id", ForeignKey("cortes_caja.id")
    )
    ticket_id: Mapped[Optional[int]] = db_column("ticket_id", ForeignKey("tickets.id"))
    before_snapshot: Mapped[Optional[str]] = db_column("before_snapshot", Text)
    after_snapshot: Mapped[Optional[str]] = db_column("after_snapshot", Text)
    reason: Mapped[Optional[str]] = db_column("reason", Text)
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )
