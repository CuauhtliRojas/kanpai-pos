# Airtable seeds

`kanpai_fixed_seed.v1.json` contiene datos de catálogo mínimos y versionables:
Roles, Unidades, zonas, estaciones, categorías, empleado inicial y mesas.
No contiene PIN, hash de PIN, tokens ni datos operativos de SQLite.

Roles y Unidades son catálogos fijos requeridos. Se crean primero mediante
upsert por `clave_rol` y `clave_unidad`; sus record IDs resuelven después los
links de Empleados e InsumosInventario. No dependen del Excel vivo.

Las mesas se inicializan con estado de referencia `Libre`. El estado real de
ocupación es operativo, el campo Airtable es readonly y el seed no lo escribe.

Los productos, insumos y recetas provienen del Excel vivo local
`airtable/imports/Kanpai.xlsx`. El archivo y el JSON generado no se versionan.
Las filas incompletas se omiten y quedan documentadas en los reportes runtime.

Normalización aplicada:

- `comida` y `yakitori` se normalizan a `Yakitori`.
- `Cocina` se asigna a `BARRA_CALIENTE`.
- En `Barra`, sake, alcohol y coctelería se asignan a `COCTELERIA`; cerveza,
  refrescos y bebidas sin alcohol a `BARRA_FRIA`. Los casos ambiguos generan
  `station_mapping_warning` y no crean una asignación.
