
Estrategia de sincronización Airtable - borrador inicial
Regla principal

Sincronización bidireccional controlada por dominio.

Airtable puede mandar hacia SQLite
Catálogos.
Configuración administrativa.
Productos.
Insumos.
Recetas.
Estaciones.
Impresoras lógicas.
Mesas como catálogo.
Destinatarios SMS.
SQLite manda hacia Airtable
Tickets.
Pagos.
Cortes.
Gastos.
Movimientos de inventario.
Producción.
Impresión.
SMS enviados.
Auditoría.
Reportes materializados.
Conflictos

Catálogos:

Campos administrativos: gana Airtable.
Campos operativos temporales: gana SQLite.
Precio cambiado en ambos lados: marcar conflicto.

Transacciones:

Gana SQLite.
Airtable no edita.
Cambio manual en Airtable debe ignorarse o marcarse como error de sync.

Inventario:

Insumos y recetas pueden venir de Airtable.
Movimientos nacen en SQLite.
Stock actual se calcula desde movimientos.

Auditoría:

Append-only desde SQLite.
Airtable solo lectura.
