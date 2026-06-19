from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UnitConversion(Base):
    __tablename__ = "unit_conversions"
    __table_args__ = (
        UniqueConstraint("from_unit_id", "to_unit_id", name="uq_unit_conversion_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    to_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    factor: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    cash_shift_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cash_shifts.id"))
    registered_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    cash_expense_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cash_expenses.id"))
    receipt_type: Mapped[str] = mapped_column(String(40), default="PURCHASE", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)
    invoice_note: Mapped[Optional[str]] = mapped_column(Text)
    amount_paid_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payment_method_id: Mapped[Optional[int]] = mapped_column(ForeignKey("payment_methods.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    lines: Mapped[list["PurchaseReceiptLine"]] = relationship(
        back_populates="purchase_receipt",
        cascade="all, delete-orphan",
    )


class PurchaseReceiptLine(Base):
    __tablename__ = "purchase_receipt_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_receipt_id: Mapped[int] = mapped_column(ForeignKey("purchase_receipts.id"), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False)
    captured_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    converted_quantity_base: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    purchase_receipt: Mapped["PurchaseReceipt"] = relationship(back_populates="lines")
    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="purchase_receipt_line",
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_base: Mapped[int] = mapped_column(Integer, nullable=False)
    signed_quantity_base: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_cost_cents_snapshot: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ticket_line_id: Mapped[Optional[int]] = mapped_column(ForeignKey("ticket_lines.id"))
    purchase_receipt_line_id: Mapped[Optional[int]] = mapped_column(ForeignKey("purchase_receipt_lines.id"))
    cash_expense_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cash_expenses.id"))
    registered_by_employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    purchase_receipt_line: Mapped[Optional["PurchaseReceiptLine"]] = relationship(
        back_populates="movements",
    )


class StockAlert(Base):
    __tablename__ = "stock_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    acknowledged_by_employee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))
