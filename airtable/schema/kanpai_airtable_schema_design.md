# Diseño conceptual Airtable - Kanpai POS - Fase 4-B

## Objetivo

Diseñar la base Airtable `Kanpai POS` como backoffice administrativo, catálogo editable, supervisión operativa y espejo consultable del POS local-first.

SQLite/FastAPI sigue siendo la fuente operativa local. Airtable no debe ser dependencia crítica para vender, cobrar, imprimir ni cerrar corte.

## Convención de tablas

Se usarán nombres claros en español, sin espacios, con PascalCase:

- Productos
- CategoriasMenu
- EstacionesProduccion
- InsumosInventario
- Tickets
- LineasTicket
- CortesCaja
- TrabajosImpresion
- EventosAuditoria

Los campos serán legibles y estables. Para campos técnicos de sincronización se usará snake_case.

## Campos técnicos estándar

Toda tabla sincronizable debe poder tener:

```text
id_sqlite
id_airtable
estado_sync
revision_remota
actualizado_sqlite_en
actualizado_airtable_en
ultimo_pull_en
ultimo_push_en
eliminado_en
activo
error_sync
No todos los campos técnicos serán visibles en vistas administrativas.

Grupos de tablas
1. Configuración
ConfiguracionNegocio

Ownership: BIDIRECTIONAL_CONTROLLED.

Campos:

id_sqlite
nombre_negocio
moneda
mensaje_ticket
logo_path
inventario_activo
zona_horaria
impuestos_activos
tasa_impuesto_bps
impuesto_incluido
etiqueta_impuesto
activo
campos_sync

Uso:

Airtable puede editar mensaje de ticket, logo, política fiscal y configuración visible. SQLite aplica estos valores localmente.

MetodosPago

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
clave_metodo
nombre
requiere_referencia
activo
campos_sync

Valores iniciales:

Efectivo
Tarjeta
Transferencia
SecuenciasFolio

Ownership: SQLITE_MASTER / READONLY_MIRROR.

Campos:

id_sqlite
clave_secuencia
prefijo
siguiente_numero
relleno
activo
campos_sync

Regla:

Airtable no debe editar siguiente_numero.

2. Salón, mesas y estaciones
ZonasServicio

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
clave_zona
nombre
orden
activo
campos_sync
Mesas

Ownership: AIRTABLE_MASTER para catálogo; SQLITE_MASTER para estado temporal.

Campos:

id_sqlite
codigo_mesa
nombre_mesa
zona
localizador
orden
estado_temporal
activo
campos_sync

Regla:

Airtable puede editar nombre, zona, orden y activo. No debe editar estado_temporal.

EstacionesProduccion

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
clave_estacion
nombre
clave_impresora
orden
activo
campos_sync
Impresoras

Ownership: AIRTABLE_MASTER para configuración; SQLITE_MASTER para trabajos.

Campos:

id_sqlite
clave_impresora
nombre
estacion
ancho_papel_mm
tipo_conexion
referencia_conexion
autocorte_activo
activo
campos_sync

Notas:

Hay 3 impresoras físicas ZKTeco/Zetko sin autocorte. Por eso autocorte_activo debe iniciar en false para esas impresoras físicas.

3. Seguridad y personal
Empleados

Ownership: BIDIRECTIONAL_CONTROLLED.

Campos visibles:

id_sqlite
codigo_empleado
nombre_completo
alias_pos
activo
pin_activo
ultimo_acceso
roles
campos_sync

Campos prohibidos en Airtable:

hash_pin
token_sesion

Regla:

Airtable puede editar nombre, alias, activo y roles. El PIN se administra localmente.

Roles

Ownership: BIDIRECTIONAL_CONTROLLED o SQLITE_MASTER controlado.

Campos:

id_sqlite
clave_rol
nombre
activo
campos_sync
Permisos

Ownership: SQLITE_MASTER recomendado.

Campos:

id_sqlite
clave_permiso
descripcion
activo
campos_sync

Regla:

Airtable puede ver permisos, pero no debe ser fuente libre de permisos críticos.

RolesEmpleado

Ownership: BIDIRECTIONAL_CONTROLLED.

Campos:

id_sqlite
empleado
rol
activo_logico
campos_sync
PermisosRol

Ownership: SQLITE_MASTER recomendado.

Campos:

id_sqlite
rol
permiso
campos_sync
4. Catálogo de venta
CategoriasMenu

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
nombre
orden
activo
campos_sync
Productos

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
sku
tipo_producto
nombre
variante
nombre_visible
categoria
precio_centavos
precio_mxn_formula
activo
visible_pos
imagen_path
campos_sync

Regla:

El POS rechaza productos con precio <= 0.

AsignacionesProductoEstacion

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
producto
estacion
es_principal
activo
campos_sync
PaquetesProducto

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
producto_paquete
modo_paquete
comportamiento_impresion
comportamiento_inventario
activo
campos_sync
ComponentesPaqueteProducto

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
paquete
producto_componente
cantidad
orden
estacion_override
asignacion_precio_centavos
visible_ticket_cliente
activo
campos_sync
GruposVarianteProducto

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
producto
nombre
seleccion_minima
seleccion_maxima
requerido
activo
campos_sync
OpcionesVarianteProducto

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
grupo_variante
producto_opcional
nombre
sku
diferencia_precio_centavos
estacion
activo
campos_sync
5. Inventario
Unidades

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
clave_unidad
nombre
familia_unidad
activo
campos_sync
ConversionesUnidad

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
unidad_origen
unidad_destino
factor
activo
campos_sync
InsumosInventario

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
codigo_insumo
nombre
unidad_base
tipo_insumo
stock_minimo
costo_unitario_centavos
costo_unitario_mxn_formula
activo
campos_sync
RecetasProducto

Ownership: AIRTABLE_MASTER.

Campos:

id_sqlite
producto
insumo
cantidad_base
porcentaje_merma
activo
campos_sync
RecepcionesCompra

Ownership: SQLITE_MASTER inicial / BIDIRECTIONAL_CONTROLLED futuro.

Campos:

id_sqlite
folio
corte_caja
registrado_por
gasto_caja
tipo_recepcion
estado
proveedor_nombre
factura_referencia
importe_pago_centavos
metodo_pago
nota
creado_en
procesado_en
campos_sync
LineasRecepcionCompra

Ownership: SQLITE_MASTER.

Campos:

id_sqlite
recepcion_compra
insumo
cantidad_capturada
unidad_capturada
cantidad_convertida_base
costo_unitario_centavos
estado
error_codigo
creado_en
campos_sync
MovimientosInventario

Ownership: READONLY_MIRROR.

Campos:

id_sqlite
folio
insumo
tipo_movimiento
cantidad_base
cantidad_con_signo_base
costo_unitario_snapshot
costo_total_centavos
linea_ticket
linea_recepcion_compra
gasto_caja
registrado_por
origen_tipo
origen_id
motivo
creado_en
campos_sync
AlertasStock

Ownership: READONLY_MIRROR.

Campos:

id_sqlite
insumo
tipo_alerta
estado
abierto_en
reconocido_en
resuelto_en
reconocido_por
umbral_cantidad
cantidad_actual
mensaje
campos_sync
6. Operación POS

Todas estas tablas son SQLite_MASTER y Airtable será READONLY_MIRROR.

CortesCaja

Campos principales:

id_sqlite
folio
estado
abierto_por
cerrado_por
abierto_en
cerrado_en
apertura_caja_centavos
declarado_caja_centavos
esperado_caja_centavos
diferencia_caja_centavos
ventas_total_centavos
efectivo_total_centavos
tarjeta_total_centavos
transferencia_total_centavos
gastos_total_centavos
neto_total_centavos
conteo_tickets
promedio_ticket_centavos
notas
campos_sync
Tickets

Campos principales:

id_sqlite
folio
corte_caja
mesa
abierto_por
mesero
cerrado_por
cancelado_por
comensales
estado
estado_pago
nota
abierto_en
inicio_cobro_en
pagado_en
cancelado_en
motivo_cancelacion
subtotal_centavos
descuento_centavos
impuesto_centavos
total_centavos
inventario_consumido_en
campos_sync
LineasTicket

Campos principales:

id_sqlite
ticket
linea_padre
paquete
componente_paquete
producto
tipo_linea
cantidad
precio_unitario_centavos
total_linea_centavos
modo_precio
nombre_producto_snapshot
sku_producto_snapshot
categoria_snapshot
estacion_snapshot
nota
estado
ronda
creado_por
cancelado_por
cancelado_autorizado_por
motivo_cancelacion
enviado_en
cancelado_en
campos_sync
SeleccionesVarianteLinea

Ownership: READONLY_MIRROR.

ModificacionesLineaTicket

Ownership: READONLY_MIRROR.

DescuentosTicket

Ownership: READONLY_MIRROR.

Pagos

Ownership: READONLY_MIRROR.

DivisionesTicket

Ownership: READONLY_MIRROR.

LineasDivisionTicket

Ownership: READONLY_MIRROR.

7. Producción
LotesComanda

Ownership: READONLY_MIRROR.

OrdenesProduccion

Ownership: READONLY_MIRROR.

Campos:

id_sqlite
lote_comanda
ticket
estacion
folio
estado
recibido_en
aceptado_en
iniciado_en
terminado_en
entregado_en
recibido_por
iniciado_por
terminado_por
entregado_por
creado_en
campos_sync
LineasOrdenProduccion

Ownership: READONLY_MIRROR.

8. Impresión
TrabajosImpresion

Ownership: READONLY_MIRROR.

Campos:

id_sqlite
folio
tipo_trabajo
impresora
clave_impresora_snapshot
ticket
corte_caja
orden_estacion
lote_comanda
contenido_snapshot
estado
intentos
tomado_en
tomado_por
ultimo_error
clave_idempotencia
impreso_en
fallido_en
siguiente_reintento_en
campos_sync

Regla:

La impresión real la hace el worker Windows desde SQLite/FastAPI. Airtable solo observa.

9. SMS y notificaciones
CanalesNotificacion

Ownership: BIDIRECTIONAL_CONTROLLED.

Campos:

id_sqlite
clave_canal
nombre
activo
campos_sync
DestinatariosNotificacion

Ownership: AIRTABLE_MASTER.

Estado: tabla nueva requerida; no existe todavía en SQLite.

Campos propuestos:

id_sqlite
canal
empleado
rol
nombre
msisdn
activo
prioridad
recibir_stock_bajo
recibir_fallo_impresion
recibir_cierre_caja
notas
campos_sync

Reglas:

msisdn debe ir en formato internacional sin +.
Ejemplo México: 52XXXXXXXXXX.
Puede apuntar a empleado, rol o ser destinatario manual.
No guardar credenciales LabsMobile.
HistorialSMS

Ownership: READONLY_MIRROR.

Fuente SQLite: notificaciones_sms.

Campos:

id_sqlite
canal
alerta_stock
empleado
msisdn
mensaje
estado
modo_prueba
respuesta_contenido
error
creado_en
enviado_en
campos_sync
10. Auditoría
EventosAuditoria

Ownership: READONLY_MIRROR.

Campos:

id_sqlite
tipo_evento
tipo_entidad
entidad_id
actor_empleado
corte_caja
ticket
snapshot_antes
snapshot_despues
motivo
creado_en
campos_sync

Regla:

Append-only desde SQLite. Airtable no edita.

11. Tablas locales que no van a Airtable
SyncInbox
SyncOutbox
SyncWatermark
SesionesEmpleado
SesionesPOS

Estas tablas son internas del backend local.

Vistas Airtable propuestas
Backoffice - Catálogos
Productos activos
Productos ocultos POS
Productos sin estación
Productos con precio 0
Categorías
Estaciones
Impresoras
Mesas activas
Insumos activos
Recetas incompletas
Administración
Empleados activos
Roles
Permisos readonly
Empleados sin rol
Destinatarios SMS activos
Operación espejo
Tickets de hoy
Tickets cobrados
Tickets cancelados
Pagos de hoy
Cortes de caja
Gastos de caja
Órdenes producción abiertas
Trabajos impresión pendientes
Trabajos impresión fallidos
Alertas stock abiertas
Historial SMS fallido
Eventos auditoría recientes
Data warehouse
Ventas por día
Ventas por producto
Ventas por categoría
Ventas por método de pago
Consumo inventario
Tiempos producción
Resumen impresión
Stock bajo
Reglas de bloqueo visual en Airtable

Campos readonly por convención:

id_sqlite en mirrors.
totales calculados por SQLite.
estados operativos de tickets.
pagos.
cortes cerrados.
movimientos inventario.
eventos auditoría.
trabajos impresión.
historial SMS.

Campos editables:

catálogos.
configuración.
productos.
insumos.
recetas.
mesas como catálogo.
impresoras como configuración.
destinatarios SMS.
