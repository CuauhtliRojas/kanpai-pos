# Cobertura del procedimiento operativo

La interfaz se alinea con el flujo operativo: mesa → cuenta → captura de productos → confirmar pedido → comanda → producción → entrega → cuenta → cobro → cierre.

| Paso | Cobertura |
| --- | --- |
| 1. Login / cajero activo | Soportado |
| 2. Apertura de caja | Soportado |
| 3. Apertura de mesa/cuenta | Soportado |
| 4. Captura de productos | Soportado en Fase 6 |
| 5. Confirmar pedido / enviar comanda | Soportado en Fase 7 si el envío responde correctamente |
| 6. Separar Cocina/Barra | Soportado con las estaciones reales devueltas por el servicio |
| 7. Producción acepta/inicia/termina | Soportado mediante transiciones estrictas y empleado activo |
| 8. Modificaciones con ticket nuevo | Pendiente |
| 9. Cancelaciones autorizadas | Pendiente |
| 10. Impresión de cuenta | Cola pendiente y reimpresión auditada soportadas; impresión física e historial completo pendientes |
| 11. Cobro y cierre | Soportado en Fase 8 cuando el pago confirma el cierre y libera la mesa |
| 12. Reportes/auditoría | Pendiente |

Agregar productos a la cuenta no confirma el pedido ni genera comandas. El envío requiere una confirmación explícita. Producción permite aceptar, iniciar y terminar con las transiciones reales del servicio.

La pantalla de Impresión consulta trabajos pendientes, reactiva fallidos vencidos y permite reimpresión con permiso y motivo. El historial general de impresos/fallidos y la confirmación física permanecen pendientes. La liberación de mesa se considera soportada únicamente cuando el pago devuelve la cuenta cerrada.
