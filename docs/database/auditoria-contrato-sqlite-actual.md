# Auditoría del contrato SQLite actual

Fecha de corte: 2026-06-19. Base auditada: commit `5765897`, antes de cualquier cambio de este trabajo.

## Tablas y columnas físicas actuales

- `audit_events`: `id`, `event_type`, `entity_type`, `entity_id`, `actor_employee_id`, `cash_shift_id`, `ticket_id`, `before_snapshot`, `after_snapshot`, `reason`, `created_at`.
- `authorizations`: `id`, `authorization_type`, `target_entity`, `target_id`, `requested_by_employee_id`, `authorized_by_employee_id`, `reason`, `status`, `created_at`.
- `business_settings`: `id`, `business_name`, `currency`, `ticket_message`, `logo_path`, `inventory_enabled`, `timezone`, `active`, `created_at`, `updated_at`.
- `cash_expenses`: `id`, `folio`, `cash_shift_id`, `description`, `category`, `payment_method_id`, `amount_cents`, `registered_by_employee_id`, `authorized_by_employee_id`, `note`, `status`, `created_at`, `updated_at`.
- `cash_shifts`: `id`, `folio`, `status`, `opened_by_employee_id`, `closed_by_employee_id`, `opened_at`, `closed_at`, `opening_cash_cents`, `declared_cash_cents`, `expected_cash_cents`, `cash_difference_cents`, `closing_note`, `sales_total_cents`, `cash_total_cents`, `card_total_cents`, `transfer_total_cents`, `expenses_total_cents`, `net_total_cents`, `ticket_count`, `average_ticket_cents`, `notes`, `created_at`, `updated_at`.
- `command_batches`: `id`, `ticket_id`, `round_number`, `batch_type`, `created_by_employee_id`, `created_at`.
- `dining_tables`: `id`, `table_code`, `display_name`, `zone_id`, `buzzer_number`, `sort_order`, `status_cache`, `active`, `created_at`, `updated_at`.
- `employee_roles`: `id`, `employee_id`, `role_id`, `created_at`, `updated_at`.
- `employees`: `id`, `employee_code`, `full_name`, `pos_alias`, `active`, campos remotos y timestamps.
- `folio_sequences`: `id`, `sequence_key`, `prefix`, `next_number`, `padding`, `active`, timestamps.
- `inventory_items`: `id`, `item_code`, `name`, `base_unit_id`, `item_type`, `minimum_stock_qty`, `unit_cost_cents`, `active`, campos remotos y timestamps.
- `inventory_movements`: `id`, `folio`, `inventory_item_id`, `movement_type`, `quantity_base`, `signed_quantity_base`, `unit_cost_cents_snapshot`, `total_cost_cents`, `ticket_line_id`, `purchase_receipt_line_id`, `cash_expense_id`, `registered_by_employee_id`, `source_type`, `source_id`, `reason`, `created_at`.
- `menu_categories`: `id`, `name`, `sort_order`, `active`, campos remotos y timestamps.
- `payment_methods`: `id`, `method_key`, `name`, `requires_reference`, `active`, timestamps.
- `payments`: `id`, `folio`, `ticket_id`, `cash_shift_id`, `payment_method_id`, `cashier_employee_id`, `amount_cents`, `received_cents`, `change_cents`, `reference`, `status`, `cancelled_by_employee_id`, `cancel_reason`, `cancelled_at`, timestamps.
- `permissions`: `id`, `permission_key`, `description`, `active`, campos remotos y timestamps.
- `pos_devices`: `id`, `device_name`, `location_label`, `is_primary`, `active`, timestamps.
- `pos_sessions`: `id`, `employee_id`, `device_id`, `status`, `opened_at`, `closed_at`, timestamps.
- `print_jobs`: `id`, `folio`, `job_type`, `printer_id`, `printer_key_snapshot`, `ticket_id`, `cash_shift_id`, `station_order_id`, `command_batch_id`, `content_snapshot`, `status`, `attempts`, `claimed_at`, `claimed_by`, `last_error`, `idempotency_key`, `printed_at`, `failed_at`, `next_retry_at`, timestamps.
- `printers`: `id`, `printer_key`, `name`, `station_id`, `paper_width_mm`, `connection_type`, `connection_ref`, `autocut_enabled`, `active`, timestamps.
- `product_package_items`: `id`, `package_id`, `component_product_id`, `quantity`, `sort_order`, `station_id_override`, `price_allocation_cents`, `visible_on_customer_ticket`, `active`, campos remotos y timestamps.
- `product_packages`: `id`, `package_product_id`, `package_mode`, `print_behavior`, `inventory_behavior`, `active`, campos remotos y timestamps.
- `product_recipes`: `id`, `product_id`, `inventory_item_id`, `quantity_base`, `waste_pct`, `active`, campos remotos y timestamps.
- `product_station_assignments`: `id`, `product_id`, `station_id`, `is_primary`, `active`, campos remotos y timestamps.
- `production_stations`: `id`, `station_key`, `name`, `printer_key`, `sort_order`, `active`, campos remotos y timestamps.
- `products`: `id`, `sku`, `product_type`, `name`, `variant`, `display_name`, `category_id`, `price_cents`, `active`, `visible_pos`, `image_path`, campos remotos y timestamps.
- `purchase_receipt_lines`: `id`, `purchase_receipt_id`, `inventory_item_id`, `captured_quantity`, `captured_unit_id`, `converted_quantity_base`, `unit_cost_cents`, `status`, `error_code`, `created_at`.
- `purchase_receipts`: `id`, `folio`, `cash_shift_id`, `registered_by_employee_id`, `cash_expense_id`, `receipt_type`, `status`, `invoice_note`, `supplier_name`, `invoice_reference`, `note`, `amount_paid_cents`, `payment_method_id`, `created_at`, `processed_at`.
- `role_permissions`: `id`, `role_id`, `permission_id`, timestamps.
- `roles`: `id`, `role_key`, `name`, `active`, campos remotos y timestamps.
- `service_zones`: `id`, `zone_key`, `name`, `sort_order`, `active`, timestamps.
- `station_order_lines`: `id`, `station_order_id`, `ticket_line_id`, `quantity`, `product_name_snapshot`, `note_snapshot`, `line_action`.
- `station_orders`: `id`, `command_batch_id`, `ticket_id`, `station_id`, `folio`, `status`, `received_at`, `accepted_at`, `started_at`, `finished_at`, `delivered_at`, `created_at`.
- `stock_alerts`: `id`, `inventory_item_id`, `alert_type`, `status`, fechas de ciclo, empleado, umbral, existencia y mensaje.
- `sync_inbox`: `id`, `source`, `entity_type`, `airtable_record_id`, `remote_revision`, `payload_json`, `status`, `error`, `received_at`, `applied_at`.
- `sync_outbox`: `id`, `event_id`, `aggregate_type`, `aggregate_id`, `event_type`, `payload_version`, `payload_json`, `status`, `attempts`, `last_error`, `airtable_record_id`, `created_at`, `sent_at`.
- `sync_watermarks`: `id`, `entity_type`, marcas de pull/push, cursor, `status`, `updated_at`.
- `table_status_events`: `id`, `table_id`, `ticket_id`, `actor_employee_id`, `from_status`, `to_status`, `reason`, `created_at`.
- `ticket_discounts`: `id`, `ticket_id`, `promotion_id`, `discount_source`, `amount_cents`, `reason`, empleados y `created_at`.
- `ticket_line_notes`: `id`, `ticket_line_id`, `note_type`, `note`, `created_by_employee_id`, `created_at`.
- `ticket_lines`: identificadores de ticket/paquete/producto, `line_type`, cantidades/importes, snapshots, `status`, ronda, cancelación y timestamps.
- `tickets`: identificadores y empleados, `guest_count`, `status`, `payment_status`, fechas de ciclo/cancelación, importes y timestamps.
- `unit_conversions`: `id`, `from_unit_id`, `to_unit_id`, `factor`, `active`, timestamps.
- `units`: `id`, `unit_key`, `name`, `unit_family`, `active`, campos remotos y timestamps.

“Campos remotos” significa `airtable_record_id`, `remote_revision`, `remote_updated_at`, `last_pulled_at`, `sync_status`; “timestamps” significa `created_at`, `updated_at`. La inspección se hizo contra `Base.metadata` y las siete revisiones Alembic existentes.

## Valores persistidos actuales por dominio

- Tickets: `OPEN`, `IN_PAYMENT`, `PAID`, `CANCELLED`; pago `UNPAID`, `PAID`, `CANCELLED`.
- Líneas: `CAPTURED`, `ENVIADO_COMANDA`, `IMPRESO`, `CANCELLED`; tipos `SIMPLE`, `PACKAGE_PARENT`, `PACKAGE_COMPONENT`; precio `NORMAL`.
- Comandas: lote `ORDER`, orden `QUEUED`, acción `ADD`.
- Impresión: tipos `COMANDA`, `TICKET`, `CORTE`, `CANCELACION_COMANDA`; estados `PENDING`, `CLAIMED`, `PRINTED`, `FAILED`, `CANCELLED`.
- Cortes: `OPEN`, `CLOSED`. Pagos/gastos: `ACTIVE`, `CANCELLED`. Métodos: `CASH`, `CARD`, `TRANSFER`.
- Inventario: `PURCHASE`, `ADJUSTMENT_IN`, `ADJUSTMENT_OUT`, `WASTE`, `SALE_CONSUMPTION`; stock `OK`, `LOW_STOCK`, `OUT_OF_STOCK`; alertas `OPEN`, `RESOLVED`; recepción `PROCESSED` (y estados internos `DRAFT`, `PENDING`).
- Catálogo/sync: `ACTIVE`, `SIMPLE`, `PACKAGE`, `FIXED_COMPONENTS`, `PRINT_COMPONENTS`, `CONSUME_COMPONENT_RECIPES`, `MASS`, `VOLUME`, `COUNT`, `OTRO`, `LOGICAL`.
- Auditoría: claves técnicas como `TICKET_OPENED`, `TICKET_LINE_ADDED`, `PACKAGE_LINE_ADDED`, `ROUND_SENT`, `PAYMENT_CREATED`, `TICKET_PAID`, `TICKET_CANCELLED`, `TICKET_LINE_CANCELLED`, `CASH_SHIFT_OPENED`, `CASH_SHIFT_CLOSED`, `CASH_EXPENSE_CREATED`, `INVENTORY_MOVEMENT_CREATED`, `PURCHASE_RECEIPT_PROCESSED`, `STOCK_ALERT_OPENED`, `STOCK_ALERT_RESOLVED`.

La base local auditada sólo tenía valores de seed: mesas `FREE`, sync `ACTIVE`, métodos `CARD/CASH/TRANSFER`, productos `SIMPLE/PACKAGE`, unidades y configuración de paquetes. La migración debe cubrir también datos transaccionales posibles en otras instalaciones.

## Dependencias

- `ticket_service`, `product_service`, `order_service`, `payment_service`, `cancellation_service` y `table_service`: ciclo completo de ticket, línea y mesa.
- `cash_shift_service`, `expense_service`, `reporting_service`: cortes, pagos, gastos y agregados.
- `print_service`, `print_queue_service` y rutas POS/printing: tipos y estados de trabajos.
- `inventory_service`, `sales_inventory_service`, `stock_alert_service`: movimientos, stock, recepciones y alertas.
- `preflight_service`: consulta todos los estados críticos y claves requeridas.
- Schemas, seed, reset, pruebas y documentos de arquitectura exponen o comparan estos valores.

## Mapa propuesto

El mapa normativo completo está en [mapa-contrato-sqlite-espanol.md](mapa-contrato-sqlite-espanol.md). Se conservarán atributos, clases, servicios, rutas y JSON keys en inglés; cambiarán tablas/columnas físicas y valores persistidos.

## Riesgos y orden recomendado

Riesgos: referencias foráneas durante renombres, índices/constraints de SQLite, instalaciones con revisión Alembic distinta, SQL manual externo, payloads frontend que comparen valores antiguos e instantáneas JSON históricas. Las instantáneas se migran sólo en sus campos estructurados conocidos; texto libre no se reescribe.

Orden: respaldo; confirmar `alembic current`; renombrar tablas; renombrar columnas; actualizar valores por dominio dentro de la misma revisión; desplegar ORM/constantes; ejecutar seed idempotente; ejecutar pruebas, preflight e inspección OpenAPI. El downgrade invierte valores, columnas y tablas.
