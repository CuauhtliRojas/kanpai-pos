# Kanpai POS - Fase 3-A: API mínima verificable

## Objetivo

Esta fase expone endpoints mínimos de lectura para validar que la API FastAPI puede consultar SQLite local correctamente.

## Alcance

Incluye endpoints para:

- Salud de API.
- Estado de base de datos.
- Resumen de seed inicial.
- Mesas.
- Categorías.
- Estaciones.
- Métodos de pago.
- Empleados.

## Regla

Esta fase no implementa lógica de negocio transaccional.

Todavía no se abren mesas, no se crean tickets y no se cobran cuentas.

Solo se valida que la API levanta, consulta SQLite y responde datos reales.

## Validación esperada

Con la API levantada, deben responder correctamente:

- `GET /health`
- `GET /api/v1/system/db`
- `GET /api/v1/system/seed-summary`
- `GET /api/v1/catalog/categories`
- `GET /api/v1/catalog/stations`
- `GET /api/v1/catalog/payment-methods`
- `GET /api/v1/operations/tables`
- `GET /api/v1/operations/employees`
