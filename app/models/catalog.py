from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RemoteCatalogMixin:
    airtable_record_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    remote_revision: Mapped[Optional[str]] = mapped_column(String(128))
    remote_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_pulled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sync_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class MenuCategory(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "menu_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class ProductionStation(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "production_stations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    station_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    printer_key: Mapped[Optional[str]] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product_assignments: Mapped[list["ProductStationAssignment"]] = relationship(
        back_populates="station",
        cascade="all, delete-orphan",
    )


class Product(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    product_type: Mapped[str] = mapped_column(String(32), default="SIMPLE", nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    variant: Mapped[Optional[str]] = mapped_column(String(120))
    display_name: Mapped[str] = mapped_column(String(220), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("menu_categories.id"))
    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    visible_pos: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500))

    category: Mapped[Optional["MenuCategory"]] = relationship(back_populates="products")
    station_assignments: Mapped[list["ProductStationAssignment"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    package_config: Mapped[Optional["ProductPackage"]] = relationship(
        back_populates="package_product",
        cascade="all, delete-orphan",
    )
    recipe_items: Mapped[list["ProductRecipe"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductStationAssignment(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "product_station_assignments"
    __table_args__ = (
        UniqueConstraint("product_id", "station_id", name="uq_product_station_assignment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("production_stations.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="station_assignments")
    station: Mapped["ProductionStation"] = relationship(back_populates="product_assignments")


class ProductPackage(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "product_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        unique=True,
        nullable=False,
    )
    package_mode: Mapped[str] = mapped_column(
        String(64),
        default="FIXED_COMPONENTS",
        nullable=False,
    )
    print_behavior: Mapped[str] = mapped_column(
        String(64),
        default="PRINT_COMPONENTS",
        nullable=False,
    )
    inventory_behavior: Mapped[str] = mapped_column(
        String(64),
        default="CONSUME_COMPONENT_RECIPES",
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    package_product: Mapped["Product"] = relationship(back_populates="package_config")
    items: Mapped[list["ProductPackageItem"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
    )


class ProductPackageItem(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "product_package_items"
    __table_args__ = (
        UniqueConstraint("package_id", "component_product_id", name="uq_package_component"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("product_packages.id"), nullable=False)
    component_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    station_id_override: Mapped[Optional[int]] = mapped_column(ForeignKey("production_stations.id"))
    price_allocation_cents: Mapped[Optional[int]] = mapped_column(Integer)
    visible_on_customer_ticket: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    package: Mapped["ProductPackage"] = relationship(back_populates="items")
    component_product: Mapped["Product"] = relationship(foreign_keys=[component_product_id])
    station_override: Mapped[Optional["ProductionStation"]] = relationship()


class Unit(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_key: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_family: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class InventoryItem(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    base_unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), default="OTRO", nullable=False)
    minimum_stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_cost_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    base_unit: Mapped["Unit"] = relationship()
    recipe_links: Mapped[list["ProductRecipe"]] = relationship(
        back_populates="inventory_item",
        cascade="all, delete-orphan",
    )


class ProductRecipe(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "product_recipes"
    __table_args__ = (
        UniqueConstraint("product_id", "inventory_item_id", name="uq_product_inventory_recipe"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    inventory_item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"), nullable=False)
    quantity_base: Mapped[int] = mapped_column(Integer, nullable=False)
    waste_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="recipe_items")
    inventory_item: Mapped["InventoryItem"] = relationship(back_populates="recipe_links")


class Employee(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    pos_alias: Mapped[Optional[str]] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list["EmployeeRole"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )


class Role(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employees: Mapped[list["EmployeeRole"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )


class Permission(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    permission_key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    roles: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
    )


class EmployeeRole(TimestampMixin, Base):
    __tablename__ = "employee_roles"
    __table_args__ = (
        UniqueConstraint("employee_id", "role_id", name="uq_employee_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="employees")


class RolePermission(TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False)

    role: Mapped["Role"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="roles")
