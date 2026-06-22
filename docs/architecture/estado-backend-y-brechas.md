# Kanpai POS - Estado del backend y brechas pendientes

## Estado actual

El backend ya cuenta con una base técnica funcional:

- Proyecto Python con `uv`.
- FastAPI levantando correctamente.
- SQLite local con SQLAlchemy.
- Alembic configurado y funcionando.
- Migraciones aplicadas.
- Seeds mínimos locales.
- Endpoints mínimos verificables por `curl`.
- Pruebas automatizadas con `pytest`.
- Revisión estática con `ruff`.

La API fue validada en puerto `8010` con:

- `GET /health`
- `GET /api/v1/system/db`
- `GET /api/v1/system/seed-summary`
- `GET /api/v1/catalog/categories`
- `GET /api/v1/operations/tables`

## Advertencia sobre datos seed

Los datos cargados por `app.db.seed` son temporales y exclusivos para desarrollo.

No representan la operación real de Kanpai.

Su función es validar estructura, relaciones, API y consultas locales antes de conectar Airtable o construir flujos POS reales.

## Estado del modelo SQLite

El modelo relacional ya cubre la estructura principal:

- Catálogos.
- Sincronización base.
- Configuración local.
- Mesas.
- Cortes.
- Tickets.
- Líneas.
- Pagos.
- Comandas.
- Impresión.
- Inventario operativo.
- Recepciones.
- Alertas de stock.
- Auditoría.

Sin embargo, el modelo todavía es estructural. Falta implementar servicios que apliquen reglas de negocio.

## Estado de FastAPI

FastAPI existe, pero todavía está en modo mínimo/verificable.

Actualmente solo expone endpoints de lectura para validar que la API consulta SQLite correctamente.

La API todavía no implementa:

- Apertura de corte.
- Apertura de mesa.
- Creación de ticket.
- Agregado de productos.
- Agregado de combos.
- Envío de ronda.
- Generación de comandas.
- Generación de trabajos de impresión.
- Inicio de cobro.
- Registro de pagos.
- Cierre de ticket.
- Liberación de mesa.
- Registro de gastos.
- Recepciones de almacén.
- Descuento de inventario.
- Cancelaciones autorizadas.
- Reimpresiones.
- Cierre de corte.

## Brechas técnicas principales

### 1. Schemas Pydantic

Falta crear schemas de entrada y salida.

Carpeta propuesta:

```text
app/schemas/
```

Deben existir schemas para:

- Mesas.
- Cortes.
- Tickets.
- Líneas.
- Productos.
- Pagos.
- Comandas.
- Impresión.
- Inventario.
- Sync.

### 2. Servicios de dominio

Falta mover la lógica de negocio fuera de rutas FastAPI.

Carpeta propuesta:

```text
app/services/
```

Servicios requeridos:

- `folio_service.py`
- `cash_shift_service.py`
- `table_service.py`
- `ticket_service.py`
- `order_service.py`
- `payment_service.py`
- `print_service.py`
- `inventory_service.py`
- `audit_service.py`
- `sync_service.py`

### 3. Endpoints operativos POS

Faltan rutas POST/PATCH reales para operar el POS.

Rutas esperadas:

- `POST /api/v1/pos/cash-shifts/open`
- `POST /api/v1/pos/tables/{table_id}/open-ticket`
- `POST /api/v1/pos/tickets/{ticket_id}/lines`
- `POST /api/v1/pos/tickets/{ticket_id}/send-round`
- `POST /api/v1/pos/tickets/{ticket_id}/start-payment`
- `POST /api/v1/pos/tickets/{ticket_id}/payments`
- `POST /api/v1/pos/tickets/{ticket_id}/close`
- `POST /api/v1/pos/cash-shifts/{cash_shift_id}/close`

### 4. Reglas de negocio

Falta implementar validaciones como:

- Solo un corte abierto.
- Mesa con máximo un ticket activo.
- Mesa se libera al cobrar.
- Ticket cobrado no se cancela desde POS normal.
- Línea capturada no permite cobrar hasta enviar ronda.
- Producto simple genera una línea.
- Producto paquete genera padre cobrable e hijas operativas.
- Línea padre de paquete no descuenta inventario.
- Componentes de paquete sí imprimen y sí descuentan inventario.
- Pago completo cierra ticket.
- Pago incompleto deja ticket en cobro.
- Gasto requiere corte abierto.
- Cancelación requiere autorización.
- Reimpresión queda auditada.

### 5. Sincronización con Airtable

Falta implementar Pull y Push.

Airtable debe mandar catálogos hacia SQLite:

- Productos.
- Precios.
- Categorías.
- Empleados.
- Roles.
- Permisos.
- Estaciones.
- Recetas.
- Combos.

SQLite debe mandar transacciones hacia Airtable:

- Tickets.
- Líneas.
- Pagos.
- Cortes.
- Gastos.
- Movimientos de inventario.
- Auditoría.
- Trabajos de impresión.

Los borrados remotos desde Airtable no deben borrar históricos en SQLite. Deben marcar registros como inactivos o `DELETED_REMOTE`.

### 6. Impresión

Falta implementar:

- Render de ticket cliente.
- Render de comanda.
- Render de corte.
- Cola de impresión.
- Daemon local de impresión.
- Reintentos.
- Marcar impresión como exitosa o fallida.
- Autocorte por impresora 58mm.
- Manejo separado de caja 58mm y estaciones 58mm.

### 7. Documentación pendiente

Debe documentarse cada función crítica con:

- Propósito.
- Entrada.
- Salida.
- Reglas de negocio.
- Errores posibles.
- Tablas que toca.
- Eventos/auditoría generada.
- Impacto en sync.
- Pruebas esperadas.

## Próximo paso recomendado

Antes de meter más endpoints, crear la capa de schemas y servicios base.

La siguiente fase debe ser:

```text
Fase 3-B: Schemas Pydantic y servicios base
```

Objetivo:

- Crear `app/schemas`.
- Crear `app/services`.
- Crear servicio de folios.
- Crear servicio de corte.
- Crear servicio de mesa.
- Probar apertura de corte con SQLite.
- Documentar cada función.
