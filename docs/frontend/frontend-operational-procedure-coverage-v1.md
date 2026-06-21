# Cobertura del procedimiento operativo

La interfaz se alinea con el flujo operativo: mesa → cuenta → captura de productos → confirmar pedido → comanda → producción → entrega → cuenta → cobro → cierre.

| Paso | Cobertura |
| --- | --- |
| 1. Login / cajero activo | Soportado |
| 2. Apertura de caja | Soportado |
| 3. Apertura de mesa/cuenta | Soportado |
| 4. Captura de productos | Completo: productos reales y confirmación del servicio |
| 5. Confirmar pedido / enviar comanda | Completo: envío explícito y comandas reales |
| 6. Separar Cocina/Barra | Soportado con las estaciones reales devueltas por el servicio |
| 7. Producción acepta/inicia/termina | Parcial: transiciones estrictas soportadas; entrega pendiente en UI |
| 8. Modificaciones con ticket nuevo | Parcial: modificación auditada y aviso a estación soportados; el contrato no crea ticket nuevo |
| 9. Cancelaciones autorizadas | Soportado con motivo, empleado activo y permiso `TICKET_CANCEL` |
| 10. Impresión de cuenta | Parcial: cola y reimpresión auditada; impresión física e historial completo pendientes |
| 11. Cobro y cierre | Soportado en Fase 8 cuando el pago confirma el cierre y libera la mesa |
| 12. Reportes/auditoría | Parcial: ventas, operación, impresión y eventos reales; categoría y paginación pendientes |
| 13. Sistema/sincronización | Completo: salud, estado, fechas, error operativo y acción manual confirmada para `ADMIN` |
| 14. Inventario operativo | Parcial: stock y alertas reales con `GET /inventory/items` y `GET /inventory/stock-alerts/active`; ajuste manual con `POST /inventory/movements` y permiso `INVENTORY_ADJUST`; historial de movimientos sin endpoint GET |
| 15. Empleados / permisos | Solo lectura: lista activos/inactivos con `GET /operations/employees`; solo `ADMIN`; roles y permisos por empleado sin contrato actual |

Agregar productos a la cuenta no confirma el pedido ni genera comandas. El envío requiere una confirmación explícita. Producción permite aceptar, iniciar y terminar con las transiciones reales del servicio.

La pantalla de Impresión consulta trabajos pendientes, reactiva fallidos vencidos y permite reimpresión con permiso y motivo. El historial general de impresos/fallidos y la confirmación física permanecen pendientes. La liberación de mesa se considera soportada únicamente cuando el pago devuelve la cuenta cerrada.

Los ajustes de pedido se realizan desde acciones compactas en cada producto. Las modificaciones quedan registradas y generan aviso para productos enviados cuando corresponde, pero el contrato actual no genera un ticket nuevo. Las cancelaciones requieren motivo y autorización mediante `TICKET_CANCEL`.

Descuentos y cortesías están soportados con `DISCOUNT_AUTHORIZE` y total confirmado por la cuenta. Promociones permanecen en preparación porque no existe contrato. Reportes y Auditoría muestran datos reales para `ADMIN`; ventas por categoría permanece pendiente.

Build Tauri verificado en Fase 14: `corepack pnpm tauri build` produce MSI e instalador NSIS en `frontend/src-tauri/target/release/bundle/`. Ver `docs/frontend/frontend-local-release-v1.md` para instrucciones completas.
