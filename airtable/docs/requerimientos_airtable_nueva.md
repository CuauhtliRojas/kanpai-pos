
Requerimientos Airtable nueva - Kanpai POS
Base

Nombre de base: Kanpai POS.

Usuarios

Airtable será usado por administradores/backoffice, no por operación crítica de caja.

Edición principal desde Airtable

Catálogos editables desde Airtable:

Productos.
Insumos.
Categorías.
Estaciones de producción.
Mesas.
Métodos de pago.
Configuración operativa.
Destinatarios SMS administrativos.
Reglas obligatorias

SQLite es maestro operativo para:

Tickets.
Líneas de ticket.
Pagos.
Cortes.
Gastos.
Movimientos de inventario.
Producción.
Trabajos de impresión.
SMS enviados.
Auditoría.

Airtable puede ser maestro de catálogos/backoffice, pero no debe permitir edición libre de transacciones generadas por SQLite.

Seguridad

No exponer en Airtable:

hash_pin.
PIN.
token_sesion.
credenciales LabsMobile.
secretos de API.
tokens Airtable.
SMS

Estado actual: el backend usa un destino único LABSMOBILE_DEFAULT_MSISDN.

Requerimiento nuevo: crear configuración de destinatarios administrativos en Airtable y sincronizarla hacia SQLite/backend.

Propuesta pendiente de diseño:

CanalesNotificacion.
DestinatariosNotificacion.
ReglasNotificacion.
HistorialSMS como espejo readonly.
Impresión

Hay 3 impresoras físicas ZKTeco/Zetko sin autocorte.

Airtable solo configura impresoras lógicas/físicas y permite supervisión.

La impresión física real la hace el worker Windows local contra SQLite/FastAPI.
