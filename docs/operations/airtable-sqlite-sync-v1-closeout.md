# Cierre de sincronización Airtable / SQLite - Kanpai POS

## Estado final

La sincronización manual entre Airtable y SQLite quedó validada bajo el contrato V1 del proyecto Kanpai POS.

El flujo validado es:

- Airtable -> SQLite para catálogo/backoffice.
- SQLite -> Airtable para operación POS.
- Sincronización manual por scripts.
- Sin activación automática en `.env` todavía.
- Sin deletes automáticos como política general de sincronización; `Empleados.roles` se reconcilia exactamente desde Airtable reemplazando sólo la relación local `roles_empleado`.

## Alcance validado

### Airtable -> SQLite

Validado para:

- Unidades
- ZonasServicio
- MetodosPago
- EstacionesProduccion
- CategoriasMenu
- Roles
- Empleados
- Mesas
- Impresoras
- InsumosInventario
- Productos
- GruposVarianteProducto
- OpcionesVarianteProducto
- AsignacionesProductoEstacion
- RecetasProducto
- CanalesNotificacion

Resultado final:

```text
Drift Airtable: OK
Seed Airtable dry-run: 0 cambios pendientes
Warnings: 0
Errores: 0
Cambios aplicados: sí
```

### SQLite -> Airtable

Validado para:

- CortesCaja
- Tickets
- LineasTicket
- Pagos
- TrabajosImpresion
- HistorialSMS
- EventosAuditoria

Resultado final dry-run:

```text
CortesCaja: creates=0 updates=0 unchanged=0 skipped=0 errors=0
Tickets: creates=0 updates=0 unchanged=0 skipped=0 errors=0
LineasTicket: creates=0 updates=0 unchanged=0 skipped=0 errors=0
Pagos: creates=0 updates=0 unchanged=0 skipped=0 errors=0
TrabajosImpresion: creates=0 updates=0 unchanged=0 skipped=0 errors=0
HistorialSMS: creates=0 updates=0 unchanged=0 skipped=0 errors=0
EventosAuditoria: creates=0 updates=0 unchanged=0 skipped=0 errors=0
Warnings: 0
Errores: 0
```

## Limpieza realizada

Se corrigió la causa raíz de duplicados locales y remotos.

### SQLite

Se eliminaron filas legacy locales:

- Grupos `Preparación`
- Opciones `Tempura` / `Asada`
- Canal duplicado `sms`
- Historial operativo local de desarrollo

Se conservó el catálogo canónico:

```text
Productos activos: 31
Insumos activos: 96
Estaciones activas: 2
Mesas activas: 17
Empleados activos: 1
Grupo variante real: BROCHETAS
Opciones reales: 6
Canal notificación real: SMS / SMS LabsMobile
```

### Airtable

Se eliminó el canal remoto legacy:

```text
sms / SMS
```

Se conservó el canal canónico:

```text
SMS / SMS LabsMobile
```

También se purgó historial operativo remoto de desarrollo:

```text
LineasTicket: 1
Pagos: 1
TrabajosImpresion: 3
HistorialSMS: 4
EventosAuditoria: 27
Tickets: 2
CortesCaja: 2
```

No se tocaron tablas de catálogo durante la purga operativa remota.

## Cambios de código / seed

Se modificaron:

```text
app/db/seed.py
airtable/seeds/kanpai_fixed_seed.v1.json
```

Cambios principales:

- Se eliminó el seed legacy `Sabores yakitori` con opciones `YAK-1`, `YAK-2`, `YAK-3`.
- Se eliminó el autogenerador de grupos `Preparación` basado en `product.variant`.
- Se corrigió `CanalesNotificacion` en el fixed seed:
  - Antes: `sms / SMS`
  - Ahora: `SMS / SMS LabsMobile`

## Contrato final de sincronización

### Fuente de verdad por dominio

Airtable es fuente de verdad para catálogo/backoffice.

SQLite es fuente de verdad operativa para el POS.

### Dirección de sincronización

```text
Airtable -> SQLite:
catálogo/backoffice

SQLite -> Airtable:
historial operativo
```

### No cubierto todavía

No queda validado como master-master total.

Pendientes explícitos:

- No hay deletes automáticos generales.
- No hay deletes de empleados ni roles en el pull; sólo se reemplaza la asignación `roles_empleado` de empleados remotos según Airtable.
- No se valida edición de productos en SQLite y subida a Airtable como flujo principal.
- No se activó auto-sync en `.env`.
- No se cerró QA visual de imagen en frontend.
- `DestinatariosNotificacion` aparece como no soportada en SQLite destino.
- `ConfiguracionNegocio` no tiene registros en el flujo actual.
- `LotesComanda`, `OrdenesEstacion` y movimientos detallados de inventario están fuera de alcance Airtable V1.

## Imagen de producto

Se validó que Airtable puede bajar imagen hacia SQLite como `image_path`, específicamente en:

```text
Productos:
- update: YAK-COC-POLL (image_path)
```

Pendiente:

- Confirmar que el endpoint usado por el frontend expone ese campo.
- Confirmar que el frontend renderiza la imagen real en POS.

## Estado recomendado antes de producción

Mantener sincronización automática apagada hasta cerrar QA visual/API.

Usar sincronización manual controlada:

- Pull para traer catálogo desde Airtable a SQLite.
- Push para subir operación desde SQLite a Airtable.

No activar `AIRTABLE_SYNC_RUN_ON_STARTUP` hasta validar comportamiento real con datos creados desde el frontend.
