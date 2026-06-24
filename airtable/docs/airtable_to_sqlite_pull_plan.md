# Plan de pull controlado Airtable -> SQLite

## Alcance y contrato observado

Esta fase trata Airtable como maestro de catálogos/configuración y conserva SQLite como runtime local-first. El pull crea o actualiza por clave natural, nunca borra registros de catálogo y no modifica endpoints, modelos, migraciones o schema Airtable. La excepción controlada es `Empleados.roles`: Airtable es fuente de verdad para la asignación de roles y el pull reemplaza la relación `roles_empleado` del empleado remoto para que coincida exactamente.

La auditoría detectó una brecha: `airtable/schema/field_map.v1.json` solo declaraba `Productos` y `Tickets`. Antes de implementar el pull se amplía esa whitelist con los campos de negocio candidatos que ya existen tanto en `kanpai_airtable_schema.v1.json` como en el ORM. Los campos no declarados se ignoran.

Los nombres físicos SQLite están traducidos mediante `db_column`; el pull usa atributos ORM (por ejemplo `Product.price_cents`) y no presupone nombres físicos en inglés.

## Mapeo candidato

| Orden | Airtable | SQLite / ORM | Clave natural | Campos sincronizables | Campos omitidos o pendientes |
| ---: | --- | --- | --- | --- | --- |
| 1 | Unidades | `unidades` / `Unit` | `clave_unidad` | nombre, familia, activo | campos técnicos |
| 2 | ZonasServicio | `zonas_servicio` / `ServiceZone` | `clave_zona` | nombre, orden, activo | campos técnicos |
| 3 | MetodosPago | `metodos_pago` / `PaymentMethod` | `clave_metodo` | nombre, requiere referencia, activo | campos técnicos |
| 4 | EstacionesProduccion | `estaciones_produccion` / `ProductionStation` | `clave_estacion` | nombre, clave impresora, orden, activo | campos técnicos |
| 5 | CategoriasMenu | `categorias_menu` / `MenuCategory` | `nombre` | orden, activo | no hay constraint único local para nombre; duplicados bloquean la entidad |
| 6 | Roles | `roles` / `Role` | `clave_rol` | nombre, activo | permisos no forman parte de esta fase |
| 7 | Empleados | `empleados` / `Employee`; `roles_empleado` / `EmployeeRole` | `codigo_empleado` | nombre, alias, activo; roles reconciliados exactamente desde Airtable | `pin_activo`, hash PIN, último acceso y sesiones son seguridad/operación local |
| 8 | Mesas | `mesas` / `DiningTable` | `codigo_mesa` | nombre, zona, localizador, orden, activo | `estado_temporal` es estado operativo SQLite-master |
| 9 | Impresoras | `impresoras` / `Printer` | `clave_impresora` | nombre, estación, ancho, conexión, autocorte, activo | trabajos/estado de impresión son operación local |
| 10 | InsumosInventario | `insumos_inventario` / `InventoryItem` | `codigo_insumo` | nombre, unidad base, tipo, stock mínimo, costo en centavos, activo | fórmula `costo_unitario_mxn` y campos técnicos |
| 11 | Productos | `productos` / `Product` | `sku` | tipo, nombre, variante, nombre visible, categoría, precio en centavos, activo, visible POS, imagen | fórmula `precio_mxn` y campos técnicos |
| 12 | AsignacionesProductoEstacion | `asignaciones_estacion_producto` / `ProductStationAssignment` | producto + estación | producto, estación, principal, activo | `nombre_registro` solo identifica el registro remoto; no tiene destino local |
| 13 | RecetasProducto | `recetas_producto` / `ProductRecipe` | producto + insumo | producto, insumo, cantidad base, merma, activo | `nombre_registro` solo identifica el registro remoto |
| 14 | CanalesNotificacion | `canales_notificacion` / `NotificationChannel` | `clave_canal` | nombre, activo | historial SMS es operación local |
| 15 | ConfiguracionNegocio | `configuracion_negocio` / `BusinessSetting` | `nombre_negocio` (singleton esperado) | moneda, mensaje, logo, inventario, zona horaria, activo (precios netos; sin impuestos en POS) | no hay constraint único; más de un registro remoto o clave local duplicada bloquea la entidad |
| -- | DestinatariosNotificacion | sin tabla SQLite | no aplicable | ninguno | pendiente de diseño; no se crean columnas o tabla en esta fase |

`ConfiguracionNegocio` se aplica al final porque no es dependencia de otro catálogo y su ausencia no debe bloquear productos/operación. El orden restante respeta todas las claves foráneas detectadas.

## Relaciones resolubles

Los links Airtable llegan como record IDs. Se construye primero un índice `record_id -> clave natural` de la tabla destino y luego se busca el ID ORM local, incluyendo registros que serían creados antes dentro de la misma transacción.

| Origen | Link | Destino / clave |
| --- | --- | --- |
| Mesas | zona | ZonasServicio / `clave_zona` |
| Impresoras | estacion | EstacionesProduccion / `clave_estacion` |
| Productos | categoria | CategoriasMenu / `nombre` |
| InsumosInventario | unidad_base | Unidades / `clave_unidad` |
| AsignacionesProductoEstacion | producto, estacion | Productos / `sku`; EstacionesProduccion / `clave_estacion` |
| RecetasProducto | producto, insumo | Productos / `sku`; InsumosInventario / `codigo_insumo` |
| Empleados | roles | Roles / `clave_rol` (reconciliación exacta contra Airtable) |

Un link requerido ausente, múltiple cuando se espera uno, apuntando fuera del conjunto leído o sin destino SQLite produce `error` para el registro y lo deja sin escribir. Un link opcional vacío se normaliza a `None`. Los backlinks automáticos no están en el field map y no se leen.

## Campos excluidos globalmente

- Técnicos Airtable: `id_sqlite`, `estado_sync`, `revision_remota`, `actualizado_sqlite_en`, `actualizado_airtable_en`, `ultimo_pull_en`, `ultimo_push_en`, `error_sync`.
- Fórmulas y backlinks automáticos.
- Timestamps, IDs, estado de sincronización y `airtable_record_id` del mixin local: no son datos de negocio autorizados por el field map.
- Estado operativo de mesa, sesiones, PIN, hash PIN, último acceso, tickets, pagos, impresión, inventario transaccional y SMS enviados.

## Pre-flight y atomicidad

Antes de planear se exige: drift con cero errores y cero warnings; lectura remota disponible; conexión SQLite y tablas destino accesibles; field map válido contra modelos y campos remotos; y seed dry-run sin errores ni creates/updates masivos. El umbral inicial de cambio masivo es 25 cambios y 20% de los upserts (se bloquea solo si se exceden ambos), configurable por CLI para operación controlada.

El modo por defecto es dry-run y abre SQLite sin mutarlo. `--execute` exige literalmente `--confirm PULL_AIRTABLE_TO_SQLITE`, aplica una sola transacción y hace rollback ante cualquier error de pre-flight o entidad. Los registros con relación inválida se reportan y se omiten; al considerarse error de entidad, impiden el commit completo. No existe código de delete.

## Riesgos y mitigaciones

- Categoría y configuración carecen de unicidad física: el pull detecta duplicados antes del upsert y bloquea ambigüedades.
- Cantidades de receta, porcentaje de merma y stock mínimo usan `Numeric(18, 6)` desde la migración `c4d8e2f1a6b9`; el pull conserva `Decimal` y rechaza valores que excedan seis decimales en vez de truncarlos. La merma se incluyó al descubrir tres valores fraccionarios que la validación anterior no alcanzaba después de fallar primero en `cantidad_base`.
- Las bajas en Airtable se representan con `activo=false`; eliminar registros remotos no elimina empleados ni roles locales.
- `Empleados.roles` se reconcilia exactamente desde Airtable: no hay deletes de empleados ni roles, pero sí se reemplazan las filas `roles_empleado` del empleado remoto para reflejar los links actuales.
- El pull bloquea planes que dejarían el sistema sin empleados activos con rol `ADMIN`.
- Cambios de clave natural se interpretan como create, no rename. Deben gestionarse explícitamente para evitar duplicados.
- La base local puede estar en uso: el execute debe hacerse con POS detenido y respaldo previo, aunque la transacción reduzca el riesgo de parcialidad.
