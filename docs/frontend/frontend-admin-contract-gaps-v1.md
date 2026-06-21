# Contratos administrativos y pendientes frontend v1

## Implementado

### Recepción de compras

`/inventory` integra `POST /api/v1/inventory/purchase-receipts` para una o más líneas. Cada línea usa un insumo real, cantidad, unidad base contractual y costo unitario. Requiere `INVENTORY_ADJUST`. El pago opcional solo se habilita con `EXPENSE_CREATE` y una forma de pago activa.

### Auditoría detallada

Los eventos vinculados permiten abrir resúmenes seguros mediante:

- `GET /api/v1/audit/tickets/{ticket_id}`;
- `GET /api/v1/audit/cash-shifts/{cash_shift_id}`.

La interfaz muestra folios, estados, fechas, importes y conteos. No presenta snapshots, metadata, payloads crudos ni identificadores internos.

## Sin contrato suficiente

- Historial general de inventario: `/api/v1/inventory/movements` solo tiene `POST`; el `GET` existente es por ticket.
- Historial general de impresión: solo existe listado pendiente y detalle por identificador.
- Impresoras: `GET /api/v1/printing/printers` no define propiedades de respuesta en OpenAPI.
- Roles/permisos por empleado: no existen rutas de consulta.
- Promociones: no existen catálogo ni aplicación.
- Ventas por categoría: no existe reporte.
- Compras pendientes: no existen `GET /purchases` ni detalle de compra; el contrato disponible procesa una recepción directa.

No se ejecutaron recepciones, ajustes, impresión ni sincronización durante esta fase.
