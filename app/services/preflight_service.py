from collections.abc import Callable

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.config import get_settings

from app.domain.constants import (
    ActiveStatus,
    CashShiftStatus,
    InventoryMovementType,
    PaymentMethodValue,
    PrintStatus,
    StockAlertStatus,
    TicketLineStatus,
    TicketStatus,
)
from app.models import (
    AuditEvent,
    CashShift,
    DiningTable,
    Employee,
    EmployeeRole,
    FolioSequence,
    InventoryItem,
    InventoryMovement,
    MenuCategory,
    Payment,
    PaymentMethod,
    Permission,
    PrintJob,
    Printer,
    Product,
    ProductRecipe,
    ProductStationAssignment,
    ProductVariantGroup,
    ProductVariantOption,
    ProductionStation,
    Role,
    RolePermission,
    StockAlert,
    Ticket,
    TicketLine,
)

ACTIVE_TICKET_STATUSES = (TicketStatus.OPEN, TicketStatus.IN_PAYMENT)
CRITICAL_TABLE_MODELS = (
    CashShift,
    Ticket,
    TicketLine,
    Payment,
    PrintJob,
    InventoryMovement,
    AuditEvent,
)
REQUIRED_FOLIOS = (
    "TICKET",
    "CORTE",
    "PAGO",
    "COMANDA",
    "MOVIMIENTO",
    "GASTO",
    "IMPRESION",
    "RECEPCION",
)
REQUIRED_PAYMENT_METHODS = (
    PaymentMethodValue.CASH,
    PaymentMethodValue.CARD,
    PaymentMethodValue.TRANSFER,
)
REQUIRED_PRINTERS = (
    "CAJA",
    "COCINA",
    "BARRA",
)
REQUIRED_PRODUCTION_STATIONS = (
    "COCINA",
    "BARRA",
)
REQUIRED_ROLES = ("ADMIN", "GERENTE", "CAJERO", "ALMACEN", "SOPORTE")
REQUIRED_PERMISSIONS = (
    "TICKET_CANCEL", "DISCOUNT_AUTHORIZE", "CASH_SHIFT_OPEN",
    "CASH_SHIFT_CLOSE", "EXPENSE_CREATE", "INVENTORY_ADJUST", "REPRINT",
    "SMS_SEND", "ADMIN_READ", "SUPPORT_ACCESS",
)
MIN_VISIBLE_PRODUCTS = 31
MIN_ACTIVE_CATEGORIES = 6
MIN_ACTIVE_TABLES = 17
MIN_ACTIVE_INVENTORY_ITEMS = 96


def _count(db: Session, model, *conditions) -> int:
    """Return a deterministic integer count for a mapped model."""
    return int(db.scalar(select(func.count(model.id)).where(*conditions)) or 0)


def _check(
    key: str, message: str, failure_message: str, query: Callable[[], bool]
) -> dict:
    """Run one critical check and isolate database failures in its result."""
    try:
        passed = query()
    except SQLAlchemyError as error:
        return {
            "key": key,
            "status": "ERROR",
            "message": f"{failure_message}: {error.__class__.__name__}",
        }
    return {
        "key": key,
        "status": "OK" if passed else "ERROR",
        "message": message if passed else failure_message,
    }


def _required_values_present(
    db: Session, model, column, required_values: tuple[str, ...], *conditions
) -> bool:
    """Check that every required seed key exists, optionally restricted by status."""
    values = set(
        db.scalars(select(column).where(column.in_(required_values), *conditions)).all()
    )
    return values == set(required_values)


def _summary(db: Session) -> dict[str, int]:
    """Build the operational counters shown by HTTP and CLI diagnostics."""
    counters = {
        "active_cash_shifts": (CashShift, CashShift.status == CashShiftStatus.OPEN),
        "open_tickets": (Ticket, Ticket.status == TicketStatus.OPEN),
        "in_payment_tickets": (Ticket, Ticket.status == TicketStatus.IN_PAYMENT),
        "pending_print_jobs": (PrintJob, PrintJob.status == PrintStatus.PENDING),
        "failed_print_jobs": (PrintJob, PrintJob.status == PrintStatus.FAILED),
        "active_stock_alerts": (StockAlert, StockAlert.status == StockAlertStatus.OPEN),
    }
    summary: dict[str, int] = {}
    for key, (model, condition) in counters.items():
        try:
            summary[key] = _count(db, model, condition)
        except SQLAlchemyError:
            summary[key] = 0
    return summary


def run_local_backend_preflight(db: Session) -> dict:
    """Evaluate schema, seed and domain invariants without modifying the database.

    Every domain invariant is critical. Failed print jobs and active stock alerts
    are operational warnings: they require attention but do not make the local
    data structurally unsafe for the next pre-sync phase.
    """
    checks: list[dict] = []
    checks.append(
        _check(
            "database",
            "Database connection is reachable",
            "Database connection is not reachable",
            lambda: db.scalar(text("SELECT 1")) == 1,
        )
    )

    def critical_tables_queryable() -> bool:
        for model in CRITICAL_TABLE_MODELS:
            db.scalar(select(model.id).limit(1))
        return True

    checks.append(
        _check(
            "migrations",
            "Critical database tables are queryable",
            "One or more critical database tables are not queryable",
            critical_tables_queryable,
        )
    )
    checks.extend(
        (
            _check(
                "seed_admin",
                "Exactly one active admin employee is present",
                "The seed must contain exactly one active admin employee",
                lambda: (
                    db.scalar(
                        select(func.count(Employee.id))
                        .join(EmployeeRole, EmployeeRole.employee_id == Employee.id)
                        .join(Role, Role.id == EmployeeRole.role_id)
                        .where(
                            Employee.active.is_(True),
                            Role.role_key == "ADMIN",
                            Role.active.is_(True),
                        )
                    )
                ) == 1,
            ),
            _check(
                "seed_payment_methods",
                "Required payment methods are present",
                "Required payment method seed is incomplete",
                lambda: _required_values_present(
                    db,
                    PaymentMethod,
                    PaymentMethod.method_key,
                    REQUIRED_PAYMENT_METHODS,
                    PaymentMethod.active.is_(True),
                ),
            ),
            _check(
                "seed_tables",
                "Exactly 17 operational dining tables are active",
                "Imported catalog must have exactly 17 active dining tables",
                lambda: _count(db, DiningTable, DiningTable.active.is_(True))
                == MIN_ACTIVE_TABLES,
            ),
            _check(
                "seed_folios",
                "Required folio sequences are present",
                "Required folio sequence seed is incomplete",
                lambda: _required_values_present(
                    db,
                    FolioSequence,
                    FolioSequence.sequence_key,
                    REQUIRED_FOLIOS,
                    FolioSequence.active.is_(True),
                ),
            ),
            _check(
                "seed_printers",
                "Required logical printers are present",
                "Required logical printer seed is incomplete",
                lambda: _required_values_present(
                    db,
                    Printer,
                    Printer.printer_key,
                    REQUIRED_PRINTERS,
                    Printer.active.is_(True),
                ),
            ),
            _check(
                "catalog_products",
                "Exactly 31 imported products are active and visible in POS",
                "Imported catalog must have exactly 31 active visible products",
                lambda: _count(
                    db, Product, Product.active.is_(True), Product.visible_pos.is_(True)
                )
                == MIN_VISIBLE_PRODUCTS,
            ),
            _check(
                "catalog_categories",
                "At least 6 menu categories are active",
                "Imported catalog has fewer than 6 active menu categories",
                lambda: _count(db, MenuCategory, MenuCategory.active.is_(True))
                >= MIN_ACTIVE_CATEGORIES,
            ),
            _check(
                "catalog_stations",
                "The 2 required production stations are the active station set",
                "Active production stations do not match the imported catalog",
                lambda: _count(
                    db, ProductionStation, ProductionStation.active.is_(True)
                )
                == len(REQUIRED_PRODUCTION_STATIONS)
                and _required_values_present(
                    db,
                    ProductionStation,
                    ProductionStation.station_key,
                    REQUIRED_PRODUCTION_STATIONS,
                    ProductionStation.active.is_(True),
                ),
            ),
            _check(
                "catalog_inventory",
                "Exactly 96 imported inventory items are active",
                "Imported catalog must have exactly 96 active inventory items",
                lambda: _count(db, InventoryItem, InventoryItem.active.is_(True))
                == MIN_ACTIVE_INVENTORY_ITEMS,
            ),
            _check(
                "seed_roles", "All supported roles are active",
                "Supported role seed is incomplete",
                lambda: _required_values_present(
                    db, Role, Role.role_key, REQUIRED_ROLES, Role.active.is_(True)
                ),
            ),
            _check(
                "seed_permissions", "All required permissions are active",
                "Required permission seed is incomplete",
                lambda: _required_values_present(
                    db, Permission, Permission.permission_key,
                    REQUIRED_PERMISSIONS, Permission.active.is_(True)
                ),
            ),
            _check(
                "admin_security_permissions",
                "ADMIN has ADMIN_READ and SUPPORT_ACCESS",
                "ADMIN lacks ADMIN_READ or SUPPORT_ACCESS",
                lambda: set(db.scalars(
                    select(Permission.permission_key)
                    .join(RolePermission, RolePermission.permission_id == Permission.id)
                    .join(Role, Role.id == RolePermission.role_id)
                    .where(
                        Role.role_key == "ADMIN",
                        Permission.permission_key.in_(("ADMIN_READ", "SUPPORT_ACCESS")),
                    )
                )) == {"ADMIN_READ", "SUPPORT_ACCESS"},
            ),
            _check(
                "no_active_demo_catalog", "No demo catalog products are active",
                "Demo catalog products remain active",
                lambda: _count(
                    db, Product, Product.sku.like("DEV-%"), Product.active.is_(True)
                ) == 0,
            ),
        )
    )
    products_with_recipe = select(ProductRecipe.product_id).where(
        ProductRecipe.active.is_(True)
    )
    missing_recipe_products = list(db.scalars(
        select(Product).where(
            Product.active.is_(True),
            Product.visible_pos.is_(True),
            Product.id.not_in(products_with_recipe),
        ).order_by(Product.sku)
    ))
    prepared_product_ids = set(db.scalars(
        select(ProductStationAssignment.product_id).where(
            ProductStationAssignment.product_id.in_(
                [product.id for product in missing_recipe_products]
            ),
            ProductStationAssignment.active.is_(True),
        )
    ))
    combo_product_ids = set(db.scalars(
        select(ProductVariantGroup.product_id)
        .join(ProductVariantOption, ProductVariantOption.variant_group_id == ProductVariantGroup.id)
        .where(
            ProductVariantGroup.active.is_(True),
            ProductVariantOption.active.is_(True),
            ProductVariantOption.product_id.is_not(None),
        )
    ))
    prepared_without_recipe = [
        product.sku for product in missing_recipe_products
        if product.id in prepared_product_ids and product.id not in combo_product_ids
    ]
    direct_without_recipe = [
        product.sku for product in missing_recipe_products
        if product.id not in prepared_product_ids
    ]
    checks.append({
        "key": "visible_product_recipes",
        "status": "ERROR" if prepared_without_recipe else "OK",
        "message": (
            "All prepared visible products have inventory recipes"
            if not prepared_without_recipe
            else "Prepared visible products without recipe: "
            + ", ".join(prepared_without_recipe)
        ),
    })
    if direct_without_recipe:
        checks.append({
            "key": "direct_products_without_recipe",
            "status": "WARNING",
            "message": "Direct-sale products without inventory recipe: "
            + ", ".join(direct_without_recipe),
        })
    duplicate_active_tables = (
        select(Ticket.table_id)
        .where(Ticket.status.in_(ACTIVE_TICKET_STATUSES))
        .group_by(Ticket.table_id)
        .having(func.count(Ticket.id) > 1)
        .subquery()
    )
    paid_recipe_tickets = (
        select(Ticket.id)
        .join(TicketLine, TicketLine.ticket_id == Ticket.id)
        .join(ProductRecipe, ProductRecipe.product_id == TicketLine.product_id)
        .where(
            Ticket.status == TicketStatus.PAID,
            Ticket.inventory_consumed_at.is_(None),
            TicketLine.status != TicketLineStatus.CANCELLED,
            ProductRecipe.active.is_(True),
        )
        .distinct()
        .subquery()
    )
    checks.extend(
        (
            _check(
                "single_open_cash_shift",
                "At most one cash shift is open",
                "More than one cash shift is open",
                lambda: (
                    _count(db, CashShift, CashShift.status == CashShiftStatus.OPEN) <= 1
                ),
            ),
            _check(
                "single_active_ticket_per_table",
                "No table has more than one active ticket",
                "A table has more than one active ticket",
                lambda: (
                    int(
                        db.scalar(
                            select(func.count()).select_from(duplicate_active_tables)
                        )
                        or 0
                    )
                    == 0
                ),
            ),
            _check(
                "paid_ticket_inventory",
                "Paid recipe tickets have consumed inventory",
                "A paid ticket with recipe lines has not consumed inventory",
                lambda: (
                    int(
                        db.scalar(select(func.count()).select_from(paid_recipe_tickets))
                        or 0
                    )
                    == 0
                ),
            ),
            _check(
                "cancelled_ticket_payments",
                "Cancelled tickets have no active payments",
                "A cancelled ticket has active payments",
                lambda: (
                    int(
                        db.scalar(
                            select(func.count(Payment.id))
                            .join(Ticket, Ticket.id == Payment.ticket_id)
                            .where(
                                Ticket.status == TicketStatus.CANCELLED,
                                Payment.status == ActiveStatus.ACTIVE,
                            )
                        )
                        or 0
                    )
                    == 0
                ),
            ),
            _check(
                "print_job_printer_snapshot",
                "All print jobs have a printer key snapshot",
                "A print job has no printer key snapshot",
                lambda: (
                    _count(
                        db,
                        PrintJob,
                        or_(
                            PrintJob.printer_key_snapshot.is_(None),
                            func.trim(PrintJob.printer_key_snapshot) == "",
                        ),
                    )
                    == 0
                ),
            ),
            _check(
                "sale_inventory_source",
                "Sale inventory movements identify their source",
                "A sale inventory movement has no source type",
                lambda: (
                    _count(
                        db,
                        InventoryMovement,
                        InventoryMovement.movement_type
                        == InventoryMovementType.SALE_CONSUMPTION,
                        or_(
                            InventoryMovement.source_type.is_(None),
                            func.trim(InventoryMovement.source_type) == "",
                        ),
                    )
                    == 0
                ),
            ),
        )
    )
    summary = _summary(db)
    if summary["failed_print_jobs"]:
        checks.append(
            {
                "key": "failed_print_jobs",
                "status": "WARNING",
                "message": f"{summary['failed_print_jobs']} print job(s) require retry or review",
            }
        )
    if summary["active_stock_alerts"]:
        checks.append(
            {
                "key": "active_stock_alerts",
                "status": "WARNING",
                "message": f"{summary['active_stock_alerts']} stock alert(s) are active",
            }
        )
    sms_settings = get_settings()
    if sms_settings.sms_enabled and (
        not sms_settings.labsmobile_user
        or not sms_settings.labsmobile_token
        or not sms_settings.labsmobile_default_msisdn
    ):
        checks.append(
            {
                "key": "labsmobile_credentials",
                "status": "WARNING",
                "message": "SMS_ENABLED=true but LabsMobile credentials or default MSISDN are missing",
            }
        )
    statuses = {check["status"] for check in checks}
    overall = (
        "ERROR" if "ERROR" in statuses else "WARNING" if "WARNING" in statuses else "OK"
    )
    return {
        "status": overall,
        "database": "sqlite",
        "checks": checks,
        "summary": summary,
    }
