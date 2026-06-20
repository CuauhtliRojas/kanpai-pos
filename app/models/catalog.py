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
    CatalogStatus,
    ItemType,
    PackageValue,
    ProductType,
)


class RemoteCatalogMixin:
    airtable_record_id: Mapped[Optional[str]] = db_column(
        "airtable_record_id", String(64), unique=True
    )
    remote_revision: Mapped[Optional[str]] = db_column("remote_revision", String(128))
    remote_updated_at: Mapped[Optional[datetime]] = db_column(
        "remote_updated_at", DateTime
    )
    last_pulled_at: Mapped[Optional[datetime]] = db_column("last_pulled_at", DateTime)
    sync_status: Mapped[str] = db_column(
        "sync_status", String(32), default=CatalogStatus.ACTIVE, nullable=False
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


class MenuCategory(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "categorias_menu"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    name: Mapped[str] = db_column("name", String(120), nullable=False)
    sort_order: Mapped[int] = db_column(
        "sort_order", Integer, default=0, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class ProductionStation(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "estaciones_produccion"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    station_key: Mapped[str] = db_column(
        "station_key", String(64), unique=True, nullable=False
    )
    name: Mapped[str] = db_column("name", String(120), nullable=False)
    printer_key: Mapped[Optional[str]] = db_column("printer_key", String(64))
    sort_order: Mapped[int] = db_column(
        "sort_order", Integer, default=0, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    product_assignments: Mapped[list["ProductStationAssignment"]] = relationship(
        back_populates="station",
        cascade="all, delete-orphan",
    )


class Product(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "productos"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    sku: Mapped[str] = db_column("sku", String(80), unique=True, nullable=False)
    product_type: Mapped[str] = db_column(
        "product_type", String(32), default=ProductType.SIMPLE, nullable=False
    )
    name: Mapped[str] = db_column("name", String(160), nullable=False)
    variant: Mapped[Optional[str]] = db_column("variant", String(120))
    display_name: Mapped[str] = db_column("display_name", String(220), nullable=False)
    category_id: Mapped[Optional[int]] = db_column(
        "category_id", ForeignKey("categorias_menu.id")
    )
    price_cents: Mapped[int] = db_column(
        "price_cents", Integer, default=0, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)
    visible_pos: Mapped[bool] = db_column(
        "visible_pos", Boolean, default=True, nullable=False
    )
    image_path: Mapped[Optional[str]] = db_column("image_path", String(500))

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
    __tablename__ = "asignaciones_estacion_producto"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "station_id", name="uq_product_station_assignment"
        ),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    product_id: Mapped[int] = db_column(
        "product_id", ForeignKey("productos.id"), nullable=False
    )
    station_id: Mapped[int] = db_column(
        "station_id", ForeignKey("estaciones_produccion.id"), nullable=False
    )
    is_primary: Mapped[bool] = db_column(
        "is_primary", Boolean, default=True, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="station_assignments")
    station: Mapped["ProductionStation"] = relationship(
        back_populates="product_assignments"
    )


class ProductPackage(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "paquetes_producto"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    package_product_id: Mapped[int] = db_column(
        "package_product_id",
        ForeignKey("productos.id"),
        unique=True,
        nullable=False,
    )
    package_mode: Mapped[str] = db_column(
        "package_mode",
        String(64),
        default=PackageValue.FIXED_COMPONENTS,
        nullable=False,
    )
    print_behavior: Mapped[str] = db_column(
        "print_behavior",
        String(64),
        default=PackageValue.PRINT_COMPONENTS,
        nullable=False,
    )
    inventory_behavior: Mapped[str] = db_column(
        "inventory_behavior",
        String(64),
        default=PackageValue.CONSUME_COMPONENT_RECIPES,
        nullable=False,
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    package_product: Mapped["Product"] = relationship(back_populates="package_config")
    items: Mapped[list["ProductPackageItem"]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
    )


class ProductPackageItem(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "componentes_paquete_producto"
    __table_args__ = (
        UniqueConstraint(
            "package_id", "component_product_id", name="uq_package_component"
        ),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    package_id: Mapped[int] = db_column(
        "package_id", ForeignKey("paquetes_producto.id"), nullable=False
    )
    component_product_id: Mapped[int] = db_column(
        "component_product_id", ForeignKey("productos.id"), nullable=False
    )
    quantity: Mapped[int] = db_column("quantity", Integer, default=1, nullable=False)
    sort_order: Mapped[int] = db_column(
        "sort_order", Integer, default=0, nullable=False
    )
    station_id_override: Mapped[Optional[int]] = db_column(
        "station_id_override", ForeignKey("estaciones_produccion.id")
    )
    price_allocation_cents: Mapped[Optional[int]] = db_column(
        "price_allocation_cents", Integer
    )
    visible_on_customer_ticket: Mapped[bool] = db_column(
        "visible_on_customer_ticket", Boolean, default=False, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    package: Mapped["ProductPackage"] = relationship(back_populates="items")
    component_product: Mapped["Product"] = relationship(
        foreign_keys=[component_product_id]
    )
    station_override: Mapped[Optional["ProductionStation"]] = relationship()


class Unit(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "unidades"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    unit_key: Mapped[str] = db_column(
        "unit_key", String(32), unique=True, nullable=False
    )
    name: Mapped[str] = db_column("name", String(80), nullable=False)
    unit_family: Mapped[str] = db_column("unit_family", String(32), nullable=False)
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)


class InventoryItem(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "insumos_inventario"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    item_code: Mapped[str] = db_column(
        "item_code", String(80), unique=True, nullable=False
    )
    name: Mapped[str] = db_column("name", String(160), nullable=False)
    base_unit_id: Mapped[int] = db_column(
        "base_unit_id", ForeignKey("unidades.id"), nullable=False
    )
    item_type: Mapped[str] = db_column(
        "item_type", String(32), default=ItemType.OTHER, nullable=False
    )
    minimum_stock_qty: Mapped[int] = db_column(
        "minimum_stock_qty", Integer, default=0, nullable=False
    )
    unit_cost_cents: Mapped[int] = db_column(
        "unit_cost_cents", Integer, default=0, nullable=False
    )
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    base_unit: Mapped["Unit"] = relationship()
    recipe_links: Mapped[list["ProductRecipe"]] = relationship(
        back_populates="inventory_item",
        cascade="all, delete-orphan",
    )


class ProductRecipe(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "recetas_producto"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "inventory_item_id", name="uq_product_inventory_recipe"
        ),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    product_id: Mapped[int] = db_column(
        "product_id", ForeignKey("productos.id"), nullable=False
    )
    inventory_item_id: Mapped[int] = db_column(
        "inventory_item_id", ForeignKey("insumos_inventario.id"), nullable=False
    )
    quantity_base: Mapped[int] = db_column("quantity_base", Integer, nullable=False)
    waste_pct: Mapped[int] = db_column("waste_pct", Integer, default=0, nullable=False)
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    product: Mapped["Product"] = relationship(back_populates="recipe_items")
    inventory_item: Mapped["InventoryItem"] = relationship(
        back_populates="recipe_links"
    )


class Employee(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "empleados"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    employee_code: Mapped[str] = db_column(
        "employee_code", String(80), unique=True, nullable=False
    )
    full_name: Mapped[str] = db_column("full_name", String(160), nullable=False)
    pos_alias: Mapped[Optional[str]] = db_column("pos_alias", String(80))
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    roles: Mapped[list["EmployeeRole"]] = relationship(
        back_populates="employee",
        cascade="all, delete-orphan",
    )


class Role(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    role_key: Mapped[str] = db_column(
        "role_key", String(80), unique=True, nullable=False
    )
    name: Mapped[str] = db_column("name", String(120), nullable=False)
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    employees: Mapped[list["EmployeeRole"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
    permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )


class Permission(RemoteCatalogMixin, TimestampMixin, Base):
    __tablename__ = "permisos"

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    permission_key: Mapped[str] = db_column(
        "permission_key", String(120), unique=True, nullable=False
    )
    description: Mapped[Optional[str]] = db_column("description", Text)
    active: Mapped[bool] = db_column("active", Boolean, default=True, nullable=False)

    roles: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
    )


class EmployeeRole(TimestampMixin, Base):
    __tablename__ = "roles_empleado"
    __table_args__ = (
        UniqueConstraint("employee_id", "role_id", name="uq_employee_role"),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    employee_id: Mapped[int] = db_column(
        "employee_id", ForeignKey("empleados.id"), nullable=False
    )
    role_id: Mapped[int] = db_column("role_id", ForeignKey("roles.id"), nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="employees")


class RolePermission(TimestampMixin, Base):
    __tablename__ = "permisos_rol"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    id: Mapped[int] = db_column("id", Integer, primary_key=True)
    role_id: Mapped[int] = db_column("role_id", ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[int] = db_column(
        "permission_id", ForeignKey("permisos.id"), nullable=False
    )

    role: Mapped["Role"] = relationship(back_populates="permissions")
    permission: Mapped["Permission"] = relationship(back_populates="roles")
