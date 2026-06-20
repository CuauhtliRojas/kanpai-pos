# Airtable UI visibility y siguiente fase

Este documento define qué debe permanecer visible en Airtable para operación de catálogo y qué debe ocultarse para evitar ruido, edición accidental o confusión con datos técnicos/sincronizados.

## Objetivo

Airtable se usa como backoffice de catálogos, configuración y supervisión.  
SQLite sigue siendo la base operativa local-first del POS.

La interfaz visible de Airtable debe exponer solo datos editables o consultables por operación.  
Las tablas técnicas, mirrors operativos y campos de sync deben ocultarse, pero nunca borrarse.

## Tablas visibles recomendadas

Estas tablas pueden quedar visibles para uso de catálogo/backoffice:

- ConfiguracionNegocio
- MetodosPago
- ZonasServicio
- Mesas
- EstacionesProduccion
- Impresoras
- Roles
- Empleados
- CategoriasMenu
- Productos
- AsignacionesProductoEstacion
- Unidades
- InsumosInventario
- RecetasProducto

Opcionales visibles solo si ya se operará SMS/notificaciones desde Airtable:

- CanalesNotificacion
- DestinatariosNotificacion

## Tablas que deben ocultarse

Estas tablas deben ocultarse en la UI normal. No deben borrarse.

### Técnicas

- Table 1
- _AirtableSchemaMigrations

### Seguridad/permisos avanzados

- Permisos

### Modelo avanzado todavía no operativo

- ConversionesUnidad
- PaquetesProducto
- ComponentesPaqueteProducto
- GruposVarianteProducto
- OpcionesVarianteProducto

### Mirror operativo desde SQLite

Estas tablas deben quedar ocultas porque serán espejo de la operación real del POS:

- Tickets
- LineasTicket
- Pagos
- CortesCaja
- TrabajosImpresion
- HistorialSMS
- EventosAuditoria

## Campos técnicos que deben ocultarse en todas las tablas visibles

Ocultar en todas las tablas donde existan:

- id_sqlite
- estado_sync
- revision_remota
- actualizado_sqlite_en
- actualizado_airtable_en
- ultimo_pull_en
- ultimo_push_en
- error_sync

Estos campos son para sincronización y diagnóstico. No deben editarse manualmente desde Airtable.

## Campos backlink automáticos que deben ocultarse

Airtable crea backlinks automáticos al crear linked records. Son útiles internamente, pero no deben mostrarse en vistas de catálogo.

Ejemplos de campos a ocultar:

- MetodosPago.Pagos
- ZonasServicio.Mesas
- Mesas.Tickets
- EstacionesProduccion.AsignacionesProductoEstacion
- EstacionesProduccion.ComponentesPaqueteProducto
- EstacionesProduccion.Impresoras
- EstacionesProduccion.OpcionesVarianteProducto
- Impresoras.TrabajosImpresion
- Roles.DestinatariosNotificacion
- Roles.Empleados
- Empleados.CortesCaja
- Empleados.CortesCaja 2
- Empleados.DestinatariosNotificacion
- Empleados.EventosAuditoria
- Empleados.HistorialSMS
- Empleados.Pagos
- Empleados.Tickets
- CategoriasMenu.Productos
- Productos.AsignacionesProductoEstacion
- Productos.ComponentesPaqueteProducto
- Productos.GruposVarianteProducto
- Productos.LineasTicket
- Productos.OpcionesVarianteProducto
- Productos.PaquetesProducto
- Productos.RecetasProducto
- PaquetesProducto.ComponentesPaqueteProducto
- GruposVarianteProducto.OpcionesVarianteProducto
- Unidades.ConversionesUnidad
- Unidades.ConversionesUnidad 2
- Unidades.InsumosInventario
- InsumosInventario.RecetasProducto
- CanalesNotificacion.DestinatariosNotificacion
- CanalesNotificacion.HistorialSMS
- Tickets.EventosAuditoria
- Tickets.LineasTicket
- Tickets.Pagos
- Tickets.TrabajosImpresion
- CortesCaja.EventosAuditoria
- CortesCaja.Pagos
- CortesCaja.Tickets

## Vistas sugeridas

Crear vistas simples por área:

- CATALOGO_POS
- CATALOGO_INVENTARIO
- CATALOGO_IMPRESION
- CATALOGO_PERSONAL
- CATALOGO_NOTIFICACIONES
- TECNICO_OCULTO

## Interfaz operativa recomendada

La interfaz principal de Airtable debería enfocarse en:

- Productos
- CategoriasMenu
- InsumosInventario
- RecetasProducto
- Mesas
- EstacionesProduccion
- Impresoras
- MetodosPago
- Empleados

No exponer en la interfaz principal:

- Tickets
- Pagos
- CortesCaja
- TrabajosImpresion
- HistorialSMS
- EventosAuditoria
- _AirtableSchemaMigrations
- campos de sync

## Estado actual

Ya existe:

- Schema Airtable aplicado.
- Migraciones Airtable tipo Alembic.
- Drift checker.
- Seed pipeline desde Excel vivo y seed fijo.
- Seed Airtable ejecutado.
- Dry-run posterior idempotente.
- Drift sin warnings ni errores.

El Excel sigue siendo fuente viva/incompleta para insumos, productos y recetas.  
El seed no borra registros si faltan en Excel. Solo hace upsert por claves naturales.

## Siguiente fase

La siguiente fase técnica es crear sincronización controlada Airtable -> SQLite para catálogos.

Orden recomendado:

1. Crear plan de pull Airtable -> SQLite.
2. Mapear tablas Airtable a tablas SQLite reales.
3. Crear preflight de sync:
   - drift Airtable OK
   - seed idempotente OK
   - SQLite disponible
   - Airtable disponible
   - field_map válido
4. Implementar pull en modo dry-run.
5. Implementar execute con confirmación explícita.
6. Validar que el POS lea catálogos reales desde SQLite.
7. Después implementar push SQLite -> Airtable para operación:
   - Tickets
   - LineasTicket
   - Pagos
   - CortesCaja
   - TrabajosImpresion
   - HistorialSMS
   - EventosAuditoria

## Dirección de sincronización por dominio

### Airtable -> SQLite

Catálogos y configuración:

- ConfiguracionNegocio
- MetodosPago
- ZonasServicio
- Mesas
- EstacionesProduccion
- Impresoras
- Roles
- Empleados
- CategoriasMenu
- Productos
- AsignacionesProductoEstacion
- Unidades
- InsumosInventario
- RecetasProducto
- CanalesNotificacion
- DestinatariosNotificacion

### SQLite -> Airtable

Operación POS:

- Tickets
- LineasTicket
- Pagos
- CortesCaja
- TrabajosImpresion
- HistorialSMS
- EventosAuditoria

## Reglas de seguridad

- No borrar registros automáticamente.
- No aceptar columnas de Airtable no declaradas en field_map.
- No sincronizar backlinks automáticos.
- No escribir campos técnicos manualmente.
- No ejecutar sync si drift falla.
- No ejecutar sync si el seed no es idempotente.
- No hacer cambios destructivos sin migración explícita.
