# Contratos API consumidos por Frontend Foundation V1

## Base URL frontend

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
Endpoints consumidos en Foundation V1
GET /health
GET /api/v1/system/airtable-sync
Endpoints existentes pero no expuestos aun en UI
POST /api/v1/system/airtable-sync/pull
POST /api/v1/system/airtable-sync/push
POST /api/v1/system/airtable-sync/run

Los endpoints de pull, push y run existen en Backend V1, pero Foundation V1 no muestra botones de ejecucion manual hasta definir confirmaciones UX, permisos operativos y estados de bloqueo para no afectar operaciones activas.
