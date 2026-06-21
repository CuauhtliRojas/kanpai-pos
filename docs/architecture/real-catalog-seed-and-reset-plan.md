# Real catalog seed and controlled reset

`airtable/imports/Kanpai.xlsx` is the catalog source of truth. The normalized seed
trims strings, handles case-insensitive aliases, ignores product rows without SKU,
maps production to exactly `COCINA` and `BARRA`, and converts `SI/NO` fields to bool.

The operational seed contains 17 active tables (`M01` through `M17`, displayed as
`Mesa 1` through `Mesa 17`) and one active operator (`ADMIN`, Administrador Kanpai)
with the ADMIN role and configured local PIN. ADMIN, GERENTE, CAJERO, ALMACEN and
SOPORTE remain seeded. All B2 permissions are explicit role-permission rows; runtime
authorization must not rely on an ADMIN fallback.

## Recipes, variants and inventory

`tempura/asada` creates one required Preparación group with two zero-price options.
The options affect command capture only; they do not duplicate products or recipes.
`no` means no variant group.

Recipe quantities are per base piece. `Product.inventory_recipe_multiplier` is a
Numeric(18,6), default 1.0. Consumption is:

`ticket line quantity * product multiplier * recipe quantity * (1 + waste fraction)`

`Merma_Pct=0.01` therefore means 1%. Yakitori is seeded with multiplier 1.0 because
the workbook does not confirm pieces per order. Set the product data to 2 or 3 once
confirmed; recipes and service code remain unchanged.

The present workbook has 165 recipe rows, but two duplicate natural keys produce 163
valid unique recipes. `MIX-BAR-004` (prepared) and `SAK-BAR-002` (direct sale) still
lack recipes. No links or quantities are inferred. Preflight intentionally blocks
promotion until those decisions are completed.

## Controlled cleanup

`scripts/reset_seed_catalog_data.py --dry-run` reports local counts without writes.
Apply requires `--confirm RESET_SQLITE_CATALOG_REAL_SEED`, creates a timestamped DB
backup in `data/backups/`, archives the old catalog, and reapplies the canonical seed.
Sales, payments, cuts and audit are preserved unless `--include-operational` is also
explicitly supplied.

`airtable/scripts/reset_airtable_catalog_plan.py` is dry-run only in B3. It reads the
schema/field map and proposes create/update/archive/unchanged; it never proposes
delete. No Airtable read or write was run in this phase.

## QA and promotion gate

Promotion requires: a corrected workbook with all recipe rows and no prepared visible
product without recipe; confirmation of Yakitori pieces per order (or explicit
acceptance of 1); reviewed SQLite dry-run; approved Airtable remote dry-run; complete
pytest collection; Ruff and diff checks. Real SQLite reset and Airtable mutation need
their separate literal confirmations.
