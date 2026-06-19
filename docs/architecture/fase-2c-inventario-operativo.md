# Kanpai POS - Fase 2-C: Inventario operativo

## Objetivo

Esta fase agrega el modelo transaccional de inventario sobre SQLite.

Incluye:

- Conversiones entre unidades.
- Recepciones de almacen.
- Lineas de recepcion.
- Movimientos de inventario.
- Alertas de stock.

## Regla arquitectonica

El stock no se guarda como campo editable.

El stock operativo se deriva de `inventory_movements` usando `signed_quantity_base`.

## Relacion con ventas

Las ventas futuras generaran movimientos de inventario desde:

- Lineas `SIMPLE`.
- Lineas `PACKAGE_COMPONENT`.

Las lineas `PACKAGE_PARENT` no descuentan inventario directamente.

## Relacion con compras

Las recepciones de almacen se registran como cabecera y lineas.

Al procesar una recepcion, se generan movimientos positivos o negativos segun el tipo.

## Relacion con gastos

Una recepcion puede asociarse a un gasto de caja si hubo pago registrado.

## Alcance no incluido

Esta fase no implementa servicios de dominio.

Esta fase no implementa endpoints.

Esta fase no ejecuta calculo real de stock; solo deja el modelo listo.
