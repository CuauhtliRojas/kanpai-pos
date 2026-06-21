# Producción e impresión frontend v1

## Alcance verificado

La implementación se basó en el OpenAPI vivo consultado el 20 de junio de 2026. No se agregaron contratos ni estados locales distintos de los expuestos por el servicio.

## Producción

- `/production` consulta las estaciones activas y usa sus nombres reales.
- Las comandas se consultan por la estación seleccionada.
- Cada tarjeta muestra folio, productos, cantidades, notas, acciones de línea no ordinarias y estado.
- Las transiciones siguen el orden estricto: `En cola` → aceptar, `Recibida` → iniciar y `En preparacion` → terminar.
- Las actualizaciones registran al empleado de la sesión y refrescan la estación actual.
- La transición de entrega existe, pero no se expone en esta fase.

Contratos consumidos:

- `GET /api/v1/catalog/stations`
- `GET /api/v1/production/station-orders?station_id={station_id}`
- `POST /api/v1/production/station-orders/{station_order_id}/receive`
- `POST /api/v1/production/station-orders/{station_order_id}/start`
- `POST /api/v1/production/station-orders/{station_order_id}/complete`

## Impresión

- `/printing` consulta la cola pendiente en orden operativo.
- Los trabajos muestran folio legible, tipo, fecha y estado confirmado.
- El reintento reactiva solo trabajos fallidos cuyo reintento ya corresponde; no fuerza todos los fallidos.
- La reimpresión exige el permiso existente `REPRINT`, empleado activo y motivo. Genera un nuevo trabajo pendiente; la interfaz no afirma que hubo impresión física.
- La consulta de la cola está disponible aunque el empleado no pueda reimprimir.

Contratos consumidos:

- `GET /api/v1/printing/jobs/pending`
- `POST /api/v1/printing/jobs/retry-failed`
- `POST /api/v1/printing/jobs/{print_job_id}/reprint`

## Pendientes conocidos

- No existe un listado general de trabajos impresos o fallidos. Esta versión solo lista pendientes.
- La confirmación de impresión física corresponde al proceso de impresión, no a esta interfaz.
- La entrega de comandas queda fuera del alcance aunque exista contrato.
- No se ejecutaron transiciones, reintentos ni reimpresiones durante la implementación para no modificar datos operativos sin seleccionar registros de prueba.
