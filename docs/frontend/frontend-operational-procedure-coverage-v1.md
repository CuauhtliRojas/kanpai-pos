# Cobertura del procedimiento operativo

La interfaz se alinea con el flujo operativo: mesa → cuenta → captura de productos → confirmar pedido → comanda → producción → entrega → cuenta → cobro → cierre.

| Paso | Cobertura |
| --- | --- |
| 1. Login / cajero activo | Soportado |
| 2. Apertura de caja | Soportado |
| 3. Apertura de mesa/cuenta | Soportado |
| 4. Captura de productos | Soportado en Fase 6 |
| 5. Confirmar pedido / enviar comanda | Soportado en Fase 7 si el envío responde correctamente |
| 6. Separar Cocina/Barra | Soportado solo cuando las comandas y el catálogo devuelven la estación |
| 7. Producción acepta/inicia/termina | Pendiente fase posterior |
| 8. Modificaciones con ticket nuevo | Pendiente |
| 9. Cancelaciones autorizadas | Pendiente |
| 10. Impresión de cuenta | Pendiente |
| 11. Cobro y cierre | Pendiente |
| 12. Reportes/auditoría | Pendiente |

Agregar productos a la cuenta no confirma el pedido ni genera comandas. En Fase 7 esa transición requiere una confirmación explícita. Producción acepta/inicia/termina permanece pendiente.
