# Fase B: cierre de contratos backend read-only

## Alcance y decisiones

| Brecha | Decision | Contrato |
|---|---|---|
| Ventas por categoria | Agregar agregacion backend sobre `TicketLine.category_id_snapshot`; solo tickets cobrados y sin componentes de paquete | `GET /api/v1/reports/sales-by-category` |
| Ledger general de inventario | Exponer historial paginado; calcular saldos antes/despues con ventana sobre el ledger completo | `GET /api/v1/inventory/movements` |
| Historial de impresion | Exponer metadatos y filtros sin `content_snapshot`, `claimed_by` ni clave de idempotencia | `GET /api/v1/printing/jobs` |
| Panel de impresoras | Formalizar el response model y derivar salud exclusivamente de configuracion y cola local | `GET /api/v1/printing/printers` |
| Empleado, roles y permisos | Leer asignaciones reales `roles_empleado` y `permisos_rol`; excluir PIN, hash y tokens | Cuatro endpoints bajo `/api/v1/operations` |
| Diagnostico existente | No crear rutas; documentar su audiencia y evitar exponerlas al operador comun | Rutas existentes de system, preflight y SMS |

No se requiere migracion: todas las columnas y relaciones necesarias ya existen. Los nombres historicos de categoria dependen del identificador capturado y del catalogo local actual porque no existe `category_name_snapshot`.

## Endpoints read-only implementados

- `GET /api/v1/reports/sales-by-category`
- `GET /api/v1/inventory/movements`
- `GET /api/v1/printing/jobs`
- `GET /api/v1/printing/printers`
- `GET /api/v1/operations/employees/{employee_id}`
- `GET /api/v1/operations/employees/{employee_id}/permissions`
- `GET /api/v1/operations/roles`
- `GET /api/v1/operations/permissions`

En ventas por categoria, `gross_sales_cents` es la suma de lineas monetarias, el descuento del ticket se prorratea conservando centavos y `share_bps` se calcula sobre venta neta. Una categoria sin catalogo resoluble se presenta como `Sin categoria`.

## Endpoints worker-only

Estas rutas pertenecen al daemon de impresion y no deben estar disponibles en la navegacion ni en permisos del operador comun:

- `GET /api/v1/printing/jobs/pending`
- `POST /api/v1/printing/jobs/claim-next`
- `POST /api/v1/printing/jobs/{print_job_id}/printed`
- `POST /api/v1/printing/jobs/{print_job_id}/failed`
- `POST /api/v1/printing/jobs/retry-failed`

`PRINTED` solo significa impresion fisica cuando el worker confirma el trabajo. El panel read-only no prueba conectividad con Windows ni con una impresora.

## Endpoints diagnostico/admin

| Endpoint | Clasificacion | Observacion |
|---|---|---|
| `GET /api/v1/system/db` | Diagnostico admin/local | Expone estado del almacenamiento local |
| `GET /api/v1/system/seed-summary` | Diagnostico admin/local | Resume catalogos seed |
| `GET /api/v1/preflight/local-backend` | Diagnostico de despliegue | Preflight tecnico, no operacion diaria |
| `GET /api/v1/notifications/sms` | Admin/configuracion | Estado del canal SMS |
| `POST /api/v1/notifications/sms/test` | Admin mutante/controlado | Puede producir un envio o simulacion; excluir de QA read-only |

La clasificacion es contractual/documental. El endurecimiento de autenticacion y autorizacion de rutas debe realizarse en una fase de seguridad separada y no se sustituye ocultando botones.

## Fuera de alcance

- Promociones mutantes o cambios a descuentos, cobro, pagos e inventario.
- Sincronizacion real con Airtable.
- Frontend visual KV2-2.
- Impresion fisica, reimpresiones y cambios de estado de la cola.
- Ventas, pagos, cancelaciones, splits, recepciones y ajustes reales.

## Riesgos

- La categoria conserva ID, pero no nombre historico; un renombre de catalogo cambia la etiqueta mostrada en reportes historicos.
- Los saldos de inventario se calculan ordenando por `created_at` e `id`; una importacion retroactiva puede cambiar saldos intermedios historicos.
- El estado de impresora es logico (`enabled`, pendientes o fallos), no telemetria fisica.
- La paginacion usa `limit`/`offset`; volumentes futuros altos pueden requerir cursor e indices revisados.
- La exposicion efectiva de rutas worker/admin requiere una politica de autenticacion y red aun pendiente.

## QA no mutante

- Validar OpenAPI y schemas de las ocho rutas.
- Consultar filtros y paginacion sobre una base de prueba aislada.
- Confirmar que historial de impresion omite `content_snapshot` y secretos de worker.
- Confirmar que empleados y permisos omiten `pin_hash`, PIN y tokens.
- Ejecutar tests automatizados con fixtures; no apuntar a la base operativa.
- Ejecutar `git diff --check` y coleccion completa de pytest.

## QA mutante controlado futuro

En una fase posterior y con base desechable: crear tickets cobrados mult categoria y con descuentos; generar movimientos de cada tipo; simular estados completos de cola con worker falso; probar autorizacion de endpoints admin/worker; y verificar rollback/restauracion. No incluir sync Airtable ni impresoras fisicas hasta contar con credenciales, aislamiento y plan de recuperacion.
