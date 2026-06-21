# Preparación E2E del frontend v1

## Estado actual

El frontend cubre el flujo operativo principal desde inicio de sesión hasta cierre de cuenta, además de producción, impresión, ajustes, administración comercial, reportes, auditoría y estado de sincronización. El build estricto de TypeScript y Vite está habilitado mediante `corepack pnpm build`.

La ventana Tauri está configurada en 1180 × 760, con mínimo de 1024 × 680. El POS cambia a tres columnas desde 1024 px y conserva scroll en mesas, productos y cuenta para evitar desbordes operativos.

## Módulos soportados

| Módulo | Estado | Alcance |
| --- | --- | --- |
| Login PIN y sesión | Completo | Inicio, recuperación y cierre de sesión |
| Caja | Completo | Apertura, resumen, gastos y cierre |
| Mesas y cuentas | Completo | Selección, apertura, continuidad y liberación confirmada |
| Productos y comandas | Completo | Captura y envío por estaciones reales |
| Producción | Parcial | Aceptar, iniciar y terminar; entrega no expuesta |
| Impresión | Parcial | Cola pendiente, reintento y reimpresión; impresión física separada |
| Pagos | Completo | Inicio de cobro, pagos y cierre confirmado |
| Modificaciones | Parcial | Registro auditado y aviso; no crea ticket nuevo |
| Cancelaciones | Completo | Motivo y permiso `TICKET_CANCEL` |
| Descuentos y cortesías | Completo | Permiso `DISCOUNT_AUTHORIZE` y total confirmado |
| Promociones | Pendiente | Sin contrato de catálogo o aplicación |
| Reportes | Parcial | Día, producto, producción e impresión; categoría pendiente |
| Auditoría | Parcial | Últimos 100 eventos, sin paginación |
| Sistema y Airtable | Completo | Salud, estado, fechas, error operativo y ejecución manual para `ADMIN` |
| Inventario | Parcial | Stock, alertas de bajo stock y ajuste manual con `INVENTORY_ADJUST`; historial sin endpoint GET |
| Empleados / Permisos | Parcial — solo lectura | Lista activos/inactivos para `ADMIN`; roles y permisos por empleado sin contrato |

## Flujo E2E manual

Usar una caja, mesa, cuenta, comanda y trabajo de impresión de prueba.

| Paso | Acción | Resultado esperado | Modifica datos |
| ---: | --- | --- | :---: |
| 1 | Iniciar sesión con empleado válido | Muestra cajero y menú permitido | Sí, sesión |
| 2 | Abrir caja | Caja abierta y resumen disponible | Sí |
| 3 | Seleccionar mesa y abrir cuenta | Mesa ocupada y cuenta activa | Sí |
| 4 | Agregar producto | Producto aparece pendiente de enviar | Sí |
| 5 | Enviar comanda | Se crean comandas por estación | Sí |
| 6 | Abrir Producción | Estaciones y comandas reales visibles | No |
| 7 | Aceptar, iniciar o terminar comanda de prueba | Estado cambia solo tras confirmación | Sí |
| 8 | Abrir Impresión | Cola pendiente real visible | No |
| 9 | Modificar o cancelar producto de prueba | Nota/motivo y autorización respetados | Sí |
| 10 | Aplicar descuento de prueba | Total cambia solo con respuesta confirmada | Sí |
| 11 | Iniciar cobro y registrar pago | Cuenta cerrada y mesa liberada | Sí |
| 12 | Abrir Reportes y Auditoría | Datos reales de solo lectura | No |
| 13 | Abrir Estado | Salud, sincronización y última actualización visibles | No |
| 14 | Ejecutar Actualizar ahora como `ADMIN` | Pide confirmación y no fuerza entrada durante operación activa | Sí, local/remoto |
| 15 | Abrir Inventario | Stock real y alertas de bajo stock visibles | No |
| 16 | Ajustar stock con insumo de prueba (solo con `INVENTORY_ADJUST`) | Cambio reflejado tras confirmación del servicio | Sí |
| 17 | Abrir Permisos como `ADMIN` | Lista de empleados activos/inactivos sin datos sensibles | No |

## Pruebas sin modificar datos

- Consultar salud y estado de sincronización.
- Recorrer navegación y comprobar accesos por permiso/rol.
- Consultar mesas, catálogos, comandas, producción y cola pendiente.
- Consultar reportes y auditoría como `ADMIN`.
- Ver totales, pagos existentes, descuentos existentes y estados vacíos.

## Acciones que modifican datos

- Login/cierre de sesión, apertura/cierre de caja y gastos.
- Apertura de cuenta, captura, envío, producción y pagos.
- Modificación, cancelación, descuento, cortesía, reintento y reimpresión.
- Sincronización manual: puede modificar datos locales y remotos; requiere `ADMIN` y confirmación explícita.

## Estado de sistema verificado

Contratos consumidos:

- `GET /health`
- `GET /api/v1/system/airtable-sync`
- `POST /api/v1/system/airtable-sync/run`

El estado devuelve habilitación, intervalo, direcciones, ejecución, fechas y último error. No devuelve conteos de pendientes o errores. Durante la revisión del 20 de junio de 2026, salud respondió correctamente y sincronización reportó un error de vínculo remoto; la UI lo presenta como “Revisar conexión o pedir ayuda” sin exponer detalles técnicos.

La acción manual real no se ejecutó durante esta fase para evitar cambios locales/remotos. El frontend envía la confirmación exigida por el contrato, no fuerza entrada durante una operación activa y vuelve a consultar el estado al terminar.

## Pendientes reales por contrato o alcance

- Catálogo y aplicación automática de promociones.
- Ventas por categoría.
- Ticket nuevo por modificación.
- Historial general de trabajos impresos/fallidos e impresión física integrada.
- Entrega de comanda desde Producción.
- Paginación/filtros de Auditoría.
- Pantallas operativas de Inventario y Permisos.

## Checklist Tauri

- [ ] Backend local iniciado y `/health` disponible.
- [ ] Ejecutar `corepack pnpm tauri dev` desde `frontend/`.
- [ ] Confirmar ventana inicial 1180 × 760 y mínimo 1024 × 680.
- [ ] Verificar topbar: cajero, mesa y estado sin recortes.
- [ ] Recorrer el menú completo; solo Inventario y Permisos deben aparecer como próximos.
- [ ] Ejecutar los pasos E2E con registros de prueba.
- [ ] Confirmar colores de peligro en cierre y cancelación.
- [ ] Confirmar estados vacíos y errores legibles.
- [ ] Probar desconexión del servicio y recuperación.
- [ ] Probar sincronización manual solo con autorización y ventana operativa controlada.
- [ ] Ejecutar `corepack pnpm build` y `git diff --check` antes de liberar.
