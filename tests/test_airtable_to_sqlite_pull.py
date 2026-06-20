from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from airtable.scripts.pull_airtable_to_sqlite import (
    PullPlan,
    TABLE_SPECS,
    apply_plan,
    build_remote_indexes,
    normalize_bool,
    normalize_decimal,
    normalize_integer,
    plan_records,
    prepare_records,
    validate_field_map,
)
from app.core.database import Base
from app.models import (
    Employee,
    EmployeeRole,
    InventoryItem,
    Product,
    ProductRecipe,
    Role,
    Unit,
)

ROOT = Path(__file__).resolve().parents[1]


def _field_map():
    import json

    return json.loads(
        (ROOT / "airtable/schema/field_map.v1.json").read_text(encoding="utf-8-sig")
    )


def _schema():
    import json

    return json.loads(
        (ROOT / "airtable/schema/kanpai_airtable_schema.v1.json").read_text(
            encoding="utf-8-sig"
        )
    )


def _engine():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def _empty_remote():
    return {spec.airtable_table: [] for spec in TABLE_SPECS}


def _prepare(remote):
    field_map = _field_map()
    indexes, index_issues = build_remote_indexes(remote, field_map)
    prepared, preparation_issues = prepare_records(remote, field_map, indexes)
    return field_map, prepared, index_issues + preparation_issues


def test_field_map_matches_airtable_schema_and_orm():
    assert validate_field_map(_field_map(), _schema()) == []


def test_type_normalization():
    assert normalize_bool(" sí ") is True
    assert normalize_bool(None) is False
    assert normalize_integer(" 12.0 ", nullable=False) == 12
    assert normalize_integer("", nullable=True) is None
    assert normalize_decimal("0.030000", nullable=False, scale=6) == Decimal(
        "0.030000"
    )
    with pytest.raises(ValueError, match="excede escala"):
        normalize_decimal("0.0000001", nullable=False, scale=6)


def test_dry_run_plans_without_writing_sqlite_and_omits_technical_fields():
    engine = _engine()
    remote = _empty_remote()
    remote["Unidades"] = [
        {
            "id": "rec-unit-kg",
            "fields": {
                "clave_unidad": " KG ",
                "nombre": " kilogramo ",
                "familia_unidad": "Masa",
                "activo": True,
                "estado_sync": "Error",
                "revision_remota": "ignored",
            },
        }
    ]
    field_map, prepared, issues = _prepare(remote)
    assert issues == []

    with Session(engine) as session:
        plan, planning_issues = plan_records(session, prepared, field_map)
        assert planning_issues == []
        assert plan["Unidades"][0].action == "create"
        assert set(plan["Unidades"][0].prepared.values) == {
            "unit_key",
            "name",
            "unit_family",
            "active",
        }
        assert session.scalar(select(func.count()).select_from(Unit)) == 0


def test_upsert_create_update_and_unchanged():
    engine = _engine()
    with Session(engine) as session, session.begin():
        session.add_all(
            [
                Unit(unit_key="KG", name="kg", unit_family="Masa", active=True),
                Unit(unit_key="ML", name="mililitro viejo", unit_family="Volumen", active=True),
            ]
        )

    remote = _empty_remote()
    remote["Unidades"] = [
        {"id": "rec-kg", "fields": {"clave_unidad": "KG", "nombre": "kg", "familia_unidad": "Masa", "activo": True}},
        {"id": "rec-ml", "fields": {"clave_unidad": "ML", "nombre": "ml", "familia_unidad": "Volumen", "activo": True}},
        {"id": "rec-pza", "fields": {"clave_unidad": "PZA", "nombre": "pza", "familia_unidad": "Conteo", "activo": True}},
    ]
    field_map, prepared, issues = _prepare(remote)
    assert issues == []
    with Session(engine) as session:
        plan, planning_issues = plan_records(session, prepared, field_map)
        assert planning_issues == []
        assert [item.action for item in plan["Unidades"]] == [
            "unchanged",
            "update",
            "create",
        ]
        with session.begin_nested():
            apply_plan(session, plan, field_map)
        session.commit()

    with Session(engine) as session:
        assert session.scalar(select(Unit.name).where(Unit.unit_key == "ML")) == "ml"
        assert session.scalar(select(func.count()).select_from(Unit)) == 3


def test_linked_record_resolves_to_sqlite_foreign_key():
    engine = _engine()
    with Session(engine) as session, session.begin():
        session.add(Unit(unit_key="KG", name="kg", unit_family="Masa", active=True))
    remote = _empty_remote()
    remote["Unidades"] = [
        {"id": "rec-unit", "fields": {"clave_unidad": "KG", "nombre": "kg", "familia_unidad": "Masa", "activo": True}}
    ]
    remote["InsumosInventario"] = [
        {
            "id": "rec-item",
            "fields": {
                "codigo_insumo": "INS-1",
                "nombre": "Arroz",
                "unidad_base": ["rec-unit"],
                "tipo_insumo": "Otro",
                "stock_minimo": 2,
                "costo_unitario_centavos": 300,
                "activo": True,
            },
        }
    ]
    field_map, prepared, issues = _prepare(remote)
    assert issues == []
    with Session(engine) as session:
        plan, planning_issues = plan_records(session, prepared, field_map)
        assert planning_issues == []
        with session.begin_nested():
            apply_plan(session, plan, field_map)
        session.commit()
    with Session(engine) as session:
        item = session.scalar(select(InventoryItem).where(InventoryItem.item_code == "INS-1"))
        assert item is not None
        assert item.base_unit.unit_key == "KG"


def test_missing_link_is_controlled_error_and_skipped():
    remote = _empty_remote()
    remote["InsumosInventario"] = [
        {
            "id": "rec-item",
            "fields": {
                "codigo_insumo": "INS-1",
                "nombre": "Arroz",
                "unidad_base": ["rec-missing"],
                "tipo_insumo": "Otro",
                "stock_minimo": 0,
                "costo_unitario_centavos": 0,
                "activo": True,
            },
        }
    ]
    _, prepared, issues = _prepare(remote)
    assert prepared["InsumosInventario"] == []
    assert [(issue.level, issue.code) for issue in issues] == [
        ("error", "invalid_remote_record")
    ]
    report_plan = PullPlan(
        {spec.airtable_table: [] for spec in TABLE_SPECS},
        issues,
        {table: len(rows) for table, rows in remote.items()},
        [],
    )
    assert report_plan.summary("InsumosInventario")["skipped"] == 1
    assert report_plan.summary("InsumosInventario")["error"] == 1


def test_fractional_inventory_and_recipe_values_are_preserved_without_truncation():
    engine = _engine()
    remote = _empty_remote()
    remote["Unidades"] = [
        {"id": "rec-unit", "fields": {"clave_unidad": "KG", "nombre": "kg", "familia_unidad": "Masa", "activo": True}}
    ]
    remote["InsumosInventario"] = [
        {
            "id": "rec-item",
            "fields": {
                "codigo_insumo": "INS-1",
                "nombre": "Arroz",
                "unidad_base": ["rec-unit"],
                "tipo_insumo": "Otro",
                "stock_minimo": 0.5,
                "costo_unitario_centavos": 0,
                "activo": True,
            },
        }
    ]
    remote["Productos"] = [
        {
            "id": "rec-product",
            "fields": {
                "sku": "PROD-1",
                "tipo_producto": "Simple",
                "nombre": "Producto",
                "nombre_visible": "Producto",
                "precio_centavos": 100,
                "activo": True,
                "visible_pos": True,
            },
        }
    ]
    remote["RecetasProducto"] = [
        {
            "id": "rec-recipe",
            "fields": {
                "producto": ["rec-product"],
                "insumo": ["rec-item"],
                "cantidad_base": 0.03,
                "porcentaje_merma": 0.015,
                "activo": True,
            },
        }
    ]
    field_map, prepared, issues = _prepare(remote)
    assert issues == []
    assert prepared["InsumosInventario"][0].values["minimum_stock_qty"] == Decimal(
        "0.500000"
    )
    assert prepared["RecetasProducto"][0].values["quantity_base"] == Decimal(
        "0.030000"
    )
    assert prepared["RecetasProducto"][0].values["waste_pct"] == Decimal(
        "0.015000"
    )
    with Session(engine) as session:
        plan, planning_issues = plan_records(session, prepared, field_map)
        assert planning_issues == []
        with session.begin_nested():
            apply_plan(session, plan, field_map)
        session.commit()
    with Session(engine) as session:
        item = session.scalar(
            select(InventoryItem).where(InventoryItem.item_code == "INS-1")
        )
        recipe = session.scalar(
            select(ProductRecipe)
            .join(Product)
            .where(Product.sku == "PROD-1")
        )
        assert item.minimum_stock_qty == Decimal("0.500000")
        assert recipe.quantity_base == Decimal("0.030000")
        assert recipe.waste_pct == Decimal("0.015000")


def test_pull_never_deletes_local_rows_or_employee_roles():
    engine = _engine()
    with Session(engine) as session, session.begin():
        admin = Role(role_key="ADMIN", name="Administrador", active=True)
        cashier = Role(role_key="CAJERO", name="Cajero", active=True)
        employee = Employee(employee_code="EMP-1", full_name="Uno", active=True)
        employee.roles.append(EmployeeRole(role=admin))
        employee.roles.append(EmployeeRole(role=cashier))
        session.add_all(
            [admin, cashier, employee, Unit(unit_key="LOCAL", name="local", unit_family="Conteo", active=True)]
        )
    remote = _empty_remote()
    remote["Roles"] = [
        {"id": "rec-admin", "fields": {"clave_rol": "ADMIN", "nombre": "Administrador", "activo": True}},
        {"id": "rec-cashier", "fields": {"clave_rol": "CAJERO", "nombre": "Cajero", "activo": True}},
    ]
    remote["Empleados"] = [
        {
            "id": "rec-employee",
            "fields": {
                "codigo_empleado": "EMP-1",
                "nombre_completo": "Uno",
                "roles": ["rec-admin"],
                "activo": True,
            },
        }
    ]
    field_map, prepared, issues = _prepare(remote)
    assert issues == []
    with Session(engine) as session:
        plan, planning_issues = plan_records(session, prepared, field_map)
        assert planning_issues == []
        assert plan["Empleados"][0].action == "unchanged"
        with session.begin_nested():
            apply_plan(session, plan, field_map)
        session.commit()
    with Session(engine) as session:
        employee = session.scalar(select(Employee).where(Employee.employee_code == "EMP-1"))
        assert {item.role.role_key for item in employee.roles} == {"ADMIN", "CAJERO"}
        assert session.scalar(select(Unit).where(Unit.unit_key == "LOCAL")) is not None
