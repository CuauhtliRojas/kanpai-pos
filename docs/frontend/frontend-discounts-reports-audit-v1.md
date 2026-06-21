# Descuentos, reportes y auditoría frontend v1

## Contratos verificados

La implementación se basó en el OpenAPI vivo consultado el 20 de junio de 2026. No se agregaron contratos ni métricas calculadas fuera de las respuestas reales.

## Descuentos y cortesías

La cuenta activa integra un apartado compacto para consultar y aplicar descuentos. La operación disponible es:

- `GET /api/v1/pos/tickets/{ticket_id}/discounts`
- `POST /api/v1/pos/tickets/{ticket_id}/discounts`
- `GET /api/v1/pos/tickets/{ticket_id}` para recuperar el total confirmado

El contrato soporta monto, porcentaje y cortesía porcentual. Aplicar exige cuenta abierta, motivo, empleado activo y permiso `DISCOUNT_AUTHORIZE`. No existe autorización por PIN o supervisor, por lo que no se simula ese flujo.

Después de una respuesta correcta se vuelve a consultar la cuenta y se muestra el total devuelto por el servicio. El frontend no calcula el total final.

No existe catálogo ni operación de promociones. El apartado Promociones permanece visible como “En preparación” y no ejecuta acciones.

## Reportes

La ruta `/reports` está disponible para el rol `ADMIN` y consulta datos del día local mediante:

- `GET /api/v1/reports/operational-summary`
- `GET /api/v1/reports/sales-by-product`
- `GET /api/v1/reports/sales-by-payment-method`
- `GET /api/v1/reports/inventory-consumption`
- `GET /api/v1/reports/production-times`
- `GET /api/v1/reports/print-jobs-summary`

La pantalla muestra ventas, número de tickets, cancelaciones, cuentas abiertas, ventas por producto, ventas por forma de pago, consumo de inventario, tiempos por estación y estado resumido de impresión. Los valores nulos de tiempo se muestran como “Sin datos”.

No existe reporte de ventas por categoría, por lo que ese apartado permanece “En preparación”.

## Auditoría

La ruta `/audit` está disponible para el rol `ADMIN` y consume:

- `GET /api/v1/audit/events?limit=100&offset=0`

Se muestran el tipo de evento, fecha y motivo cuando existe. No se muestran identificadores internos ni snapshots. El contrato devuelve eventos reales de cancelaciones, reimpresiones, descuentos, cortesías y otras operaciones auditadas.

## Validación de datos

Las consultas de solo lectura devolvieron datos reales para resumen operativo, ventas por producto, tiempos de producción, impresión y auditoría. No se aplicó ningún descuento ni cortesía durante la implementación.

## Pendientes

- Promociones automáticas o por catálogo: sin contrato.
- Ventas por categoría: sin contrato.
- Auditoría: se muestran los 100 eventos más recientes; paginación y filtros quedan para una fase posterior.
