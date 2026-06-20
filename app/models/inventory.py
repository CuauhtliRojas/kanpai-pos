from datetime import datetime
from typing import Optional

from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.domain.database_contract import db_column
from app.domain.constants import (
    ReceiptStatus,
    StockAlertStatus,
)


class UnitConversion(Base):
    __tablename__ = "conversiones_unidad"
    __table_args__ = (
        UniqueConstraint("from_unit_id", "to_unit_id", name="uq_unit_conversion_pair"),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    from_unit_id: Mapped[int] = db_column(
        "from_unit_id", ForeignKey("unidades.id"), nullable=False
    )
    to_unit_id: Mapped[int] = db_column(
        "to_unit_id", ForeignKey("unidades.id"), nullable=False
    )
    factor: Mapped[Decimal] = db_column("factor", Numeric(18, 6), nullable=False)
    active: Mapped[bool] = db_column("active", default=True, nullable=False)
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


class PurchaseReceipt(Base):
    __tablename__ = "recepciones_compra"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    cash_shift_id: Mapped[Optional[int]] = db_column(
        "cash_shift_id", ForeignKey("cortes_caja.id")
    )
    registered_by_employee_id: Mapped[int] = db_column(
        "registered_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    cash_expense_id: Mapped[Optional[int]] = db_column(
        "cash_expense_id", ForeignKey("gastos_caja.id")
    )
    receipt_type: Mapped[str] = db_column(
        "receipt_type", String(40), default="Compra", nullable=False
    )
    status: Mapped[str] = db_column(
        "status", String(32), default=ReceiptStatus.DRAFT, nullable=False
    )
    invoice_note: Mapped[Optional[str]] = db_column("invoice_note", Text)
    supplier_name: Mapped[Optional[str]] = db_column("supplier_name", String(160))
    invoice_reference: Mapped[Optional[str]] = db_column(
        "invoice_reference", String(120)
    )
    note: Mapped[Optional[str]] = db_column("note", Text)
    amount_paid_cents: Mapped[int] = db_column(
        "amount_paid_cents", Integer, default=0, nullable=False
    )
    payment_method_id: Mapped[Optional[int]] = db_column(
        "payment_method_id", ForeignKey("metodos_pago.id")
    )
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = db_column("processed_at", DateTime)

    lines: Mapped[list["PurchaseReceiptLine"]] = relationship(
        back_populates="purchase_receipt",
        cascade="all, delete-orphan",
    )


class PurchaseReceiptLine(Base):
    __tablename__ = "lineas_recepcion_compra"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    purchase_receipt_id: Mapped[int] = db_column(
        "purchase_receipt_id", ForeignKey("recepciones_compra.id"), nullable=False
    )
    inventory_item_id: Mapped[int] = db_column(
        "inventory_item_id", ForeignKey("insumos_inventario.id"), nullable=False
    )
    captured_quantity: Mapped[Decimal] = db_column(
        "captured_quantity", Numeric(18, 6), nullable=False
    )
    captured_unit_id: Mapped[int] = db_column(
        "captured_unit_id", ForeignKey("unidades.id"), nullable=False
    )
    converted_quantity_base: Mapped[Decimal] = db_column(
        "converted_quantity_base", Numeric(18, 6), nullable=False
    )
    unit_cost_cents: Mapped[int] = db_column(
        "unit_cost_cents", Integer, default=0, nullable=False
    )
    status: Mapped[str] = db_column(
        "status", String(32), default=ReceiptStatus.PENDING, nullable=False
    )
    error_code: Mapped[Optional[str]] = db_column("error_code", String(120))
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )

    purchase_receipt: Mapped["PurchaseReceipt"] = relationship(back_populates="lines")
    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="purchase_receipt_line",
    )


class InventoryMovement(Base):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    folio: Mapped[str] = db_column("folio", String(40), unique=True, nullable=False)
    inventory_item_id: Mapped[int] = db_column(
        "inventory_item_id", ForeignKey("insumos_inventario.id"), nullable=False
    )
    movement_type: Mapped[str] = db_column("movement_type", String(64), nullable=False)
    quantity_base: Mapped[Decimal] = db_column(
        "quantity_base", Numeric(18, 6), nullable=False
    )
    signed_quantity_base: Mapped[Decimal] = db_column(
        "signed_quantity_base", Numeric(18, 6), nullable=False
    )
    unit_cost_cents_snapshot: Mapped[int] = db_column(
        "unit_cost_cents_snapshot", Integer, default=0, nullable=False
    )
    total_cost_cents: Mapped[int] = db_column(
        "total_cost_cents", Integer, default=0, nullable=False
    )
    ticket_line_id: Mapped[Optional[int]] = db_column(
        "ticket_line_id", ForeignKey("lineas_ticket.id")
    )
    purchase_receipt_line_id: Mapped[Optional[int]] = db_column(
        "purchase_receipt_line_id", ForeignKey("lineas_recepcion_compra.id")
    )
    cash_expense_id: Mapped[Optional[int]] = db_column(
        "cash_expense_id", ForeignKey("gastos_caja.id")
    )
    registered_by_employee_id: Mapped[int] = db_column(
        "registered_by_employee_id", ForeignKey("empleados.id"), nullable=False
    )
    source_type: Mapped[Optional[str]] = db_column("source_type", String(64))
    source_id: Mapped[Optional[int]] = db_column("source_id", Integer)
    reason: Mapped[Optional[str]] = db_column("reason", Text)
    created_at: Mapped[datetime] = db_column(
        "created_at", DateTime, default=datetime.utcnow, nullable=False
    )

    purchase_receipt_line: Mapped[Optional["PurchaseReceiptLine"]] = relationship(
        back_populates="movements",
    )


class StockAlert(Base):
    __tablename__ = "alertas_stock"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    inventory_item_id: Mapped[int] = db_column(
        "inventory_item_id", ForeignKey("insumos_inventario.id"), nullable=False
    )
    alert_type: Mapped[str] = db_column("alert_type", String(64), nullable=False)
    status: Mapped[str] = db_column(
        "status", String(32), default=StockAlertStatus.OPEN, nullable=False
    )
    opened_at: Mapped[datetime] = db_column(
        "opened_at", DateTime, default=datetime.utcnow, nullable=False
    )
    acknowledged_at: Mapped[Optional[datetime]] = db_column("acknowledged_at", DateTime)
    resolved_at: Mapped[Optional[datetime]] = db_column("resolved_at", DateTime)
    acknowledged_by_employee_id: Mapped[Optional[int]] = db_column(
        "acknowledged_by_employee_id", ForeignKey("empleados.id")
    )
    threshold_quantity: Mapped[Decimal] = db_column(
        "threshold_quantity", Numeric(18, 6), default=0, nullable=False
    )
    current_quantity: Mapped[Decimal] = db_column(
        "current_quantity", Numeric(18, 6), default=0, nullable=False
    )
    message: Mapped[str] = db_column("message", Text, default="", nullable=False)
