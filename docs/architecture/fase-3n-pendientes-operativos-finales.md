# Fase 3-N: pendientes operativos finales

La fase agrega autenticación local, órdenes armables, cuentas divididas, SMS y el adaptador físico de impresión sin cambiar el carácter local-first del backend.

## Decisiones

- El PIN se deriva con PBKDF2-SHA256, salt aleatorio y 310 000 iteraciones. Las sesiones son revocables y expiran.
- Los endpoints históricos conservan `employee_id`. El frontend obtiene la identidad con `/auth/me` y envía ese identificador hasta activar middleware global.
- Las variantes guardan snapshots en la línea: nombre, SKU, delta y estación. Así, cambios futuros de catálogo no alteran tickets históricos.
- Todo pago, normal o asociado a una división, vive en `pagos`. El cierre sigue dependiendo de la suma activa contra el total del ticket.
- LabsMobile es un adaptador tolerante a fallos. Nunca se guarda el token y un error no revierte ventas o inventario.
- La API solo encola y confirma trabajos. El worker Windows es quien conoce nombres de impresoras y `pywin32`.

## Persistencia

La migración `f3n7a1b2c3d4` crea `sesiones_empleado`, `grupos_variante_producto`, `opciones_variante_producto`, `selecciones_variante_linea`, `divisiones_ticket`, `lineas_division_ticket`, `canales_notificacion` y `notificaciones_sms`; además amplía `empleados` y `pagos`. Todos los identificadores físicos permanecen en español.

## Límites intencionales

No se conecta Airtable, no se agrega frontend y no se exige sesión global. La impresión física requiere Windows y `pywin32` solo en el entorno del worker.
