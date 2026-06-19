# Kanpai POS - Fase 2-D: Seeds mínimos locales

## Objetivo

Esta fase agrega un seed inicial idempotente para poblar datos mínimos que permiten validar el modelo local sin depender todavía de Airtable.

## Alcance

Incluye:

- Configuración base del negocio.
- Secuencias de folios.
- Métodos de pago.
- Zonas de servicio.
- Mesas base.
- Dispositivo POS local.
- Unidades base.
- Categorías iniciales.
- Estaciones de producción.
- Roles.
- Permisos.
- Empleado administrador inicial.

## Regla de idempotencia

El seed puede ejecutarse varias veces sin duplicar registros.

Cada entidad se identifica por llaves naturales como:

- `sequence_key`
- `method_key`
- `zone_key`
- `table_code`
- `unit_key`
- `station_key`
- `role_key`
- `permission_key`
- `employee_code`

## Relación con Airtable

Estos seeds sirven para desarrollo local y arranque inicial.

Cuando se implemente sincronización Pull, Airtable podrá reemplazar o actualizar los catálogos administrativos.

SQLite seguirá conservando datos históricos y operativos.
