# Kanpai POS - Fase 2-B: Modelo operativo POS

## Objetivo

Esta fase agrega el nucleo transaccional local del POS sobre SQLite.

Incluye:

- Configuracion operativa local.
- Secuencias de folios.
- Dispositivos y sesiones POS.
- Zonas y mesas.
- Cortes de caja.
- Tickets.
- Lineas de ticket.
- Notas/modificaciones.
- Descuentos.
- Metodos de pago.
- Pagos.
- Comandas por ronda.
- Ordenes por estacion.
- Lineas de comanda.
- Impresoras.
- Cola de impresion.
- Gastos de caja.
- Autorizaciones.
- Auditoria.

## Regla arquitectonica

SQLite es la fuente de verdad para toda operacion transaccional.

Airtable no decide estados operativos. Airtable recibira estas transacciones despues, por sincronizacion Push.

## Decision de combos

La venta de combos se soporta desde `ticket_lines` con jerarquia:

- `PACKAGE_PARENT`: linea cobrable del paquete.
- `PACKAGE_COMPONENT`: linea operativa hija para comanda e inventario.
- `SIMPLE`: producto normal.

El ticket suma `SIMPLE` y `PACKAGE_PARENT`.

La produccion e inventario usan `SIMPLE` y `PACKAGE_COMPONENT`.

## Alcance no incluido

Esta fase no crea servicios de dominio ni endpoints FastAPI.

Esta fase no procesa inventario operativo todavia. Los movimientos de inventario quedan para Fase 2-C.
