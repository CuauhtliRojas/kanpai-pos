# Kanpai POS - Fase 2-A: Modelo base de catalogos y sincronizacion

## Objetivo

Esta fase introduce el primer bloque persistente del modelo relacional local en SQLite.

El alcance se limita a:

- Catalogos administrativos replicados desde Airtable hacia SQLite.
- Productos simples y paquetes/combos.
- Categorias de menu.
- Estaciones de produccion.
- Insumos, unidades y recetas.
- Empleados, roles y permisos.
- Tablas base de sincronizacion Pull/Push.

## Regla de autoridad

Airtable es fuente de verdad para catalogos administrativos:

- Productos.
- Precios.
- Categorias.
- Estaciones.
- Empleados.
- Roles.
- Permisos.
- Insumos.
- Recetas.
- Paquetes/combos.

SQLite es fuente de verdad para operacion transaccional:

- Tickets.
- Lineas de venta.
- Comandas.
- Pagos.
- Cortes.
- Gastos.
- Inventario operativo.
- Auditoria.
- Cola de impresion.

## Decision importante

Los combos se modelan como productos vendibles tipo PACKAGE.

Un paquete tiene:

- Una linea padre cobrable en el ticket.
- Componentes hijos operativos para comanda e inventario.

Ejemplo:

Producto comercial:
- Chela + Sake

Componentes:
- Chela
- Sake

El POS cobra el precio del paquete, pero imprime y descuenta inventario por componente.
