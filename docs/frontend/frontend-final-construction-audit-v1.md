# Auditoría final de construcción frontend V1

Fecha: 2026-06-20 22:51:10

## Commit y estado

### Últimos commits

`	ext
117b8bb feat(frontend): add advanced ticket and admin flows
c61c988 chore(frontend): complete backend contract coverage audit
ac0e426 chore(frontend): add local Tauri release readiness
03f1f31 feat(frontend): add inventory and employee security views
0e472e3 feat(frontend): add system sync status and E2E readiness
ce589ad feat(frontend): add discounts reports and audit views
6288e7b feat(frontend): add ticket modifications and cancellations
ab2d408 feat(frontend): add production and printing operations

Estado Git al auditar
Working tree limpio.
Resultado ejecutivo

OpenAPI disponible: True

Rutas OpenAPI detectadas: 71

Operaciones OpenAPI detectadas: 74

Resultado corepack pnpm build: exitCode=1

Resultado git diff --check: exitCode=0

Recomendación:

NO pasar todavía a pruebas SQLite ↔ Airtable si hay endpoints pendientes transaccionales o si build/diff check falla.
Módulos frontend detectados

- audit
- auth
- cash
- checkout
- commands
- discounts
- inventory
- operations
- payments
- printing
- production
- products
- purchases
- reports
- security
- system
- tables
- ticket-adjustments
- ticket-cancel
- tickets
- ticket-split
- variants

Rutas backend detectadas

- __init__.py
- audit.py
- auth.py
- catalog.py
- inventory.py
- notifications.py
- operations.py
- pos.py
- preflight.py
- printing.py
- production.py
- reports.py
- splits.py
- system.py

Documentos frontend detectados

- frontend-admin-contract-gaps-v1.md
- frontend-advanced-ticket-flows-v1.md
- frontend-api-contracts-v1.md
- frontend-auth-session-v1.md
- frontend-backend-contract-coverage-v1.md
- frontend-brand-assets-v1.md
- frontend-cash-shift-v1.md
- frontend-discounts-reports-audit-v1.md
- frontend-e2e-readiness-v1.md
- frontend-endpoint-consumption-map-v1.md
- frontend-foundation-v1-plan.md
- frontend-inventory-security-v1.md
- frontend-local-release-v1.md
- frontend-operational-procedure-coverage-v1.md
- frontend-permissions-navigation-v1.md
- frontend-pos-checkout-payments-v1.md
- frontend-pos-products-v1.md
- frontend-pos-send-command-v1.md
- frontend-pos-tables-v1.md
- frontend-product-function-model-v1.md
- frontend-production-printing-v1.md
- frontend-qa-foundation-v1.md
- frontend-stack-decisions.md
- frontend-ticket-adjustments-v1.md
- frontend-visual-identity-v1.md

Cobertura por dominio
DominioTotalCubierto exactoParcial / revisarPendienteNo aplica
| Caja | 6 | 3 | 3 | 0 | 0 |
| Catalogo | 10 | 6 | 4 | 0 | 0 |
| Impresion | 10 | 3 | 7 | 0 | 0 |
| Inventario y compras | 6 | 5 |  | 0 | 0 |
| POS | 29 | 5 | 24 | 0 | 0 |
| Preflight / notificaciones | 3 | 0 | 0 | 0 | 3 |
| Reportes y auditoria | 2 | 2 | 0 | 0 | 0 |
| Seguridad | 4 | 4 | 0 | 0 | 0 |
| Sistema y sincronizacion | 4 |  | 3 | 0 | 0 |
Matriz endpoint por endpoint
DominioMétodoEndpointÁrea frontend esperadaEstado
| Caja | GET | $(@{Domain=Caja; Method=GET; Path=/api/v1/audit/cash-shifts/{cash_shift_id}; FrontendArea=cash; Status=parcial / revisar uso exacto}.Path) | cash | parcial / revisar uso exacto |
| Caja | POST | $(@{Domain=Caja; Method=POST; Path=/api/v1/pos/cash-expenses; FrontendArea=cash; Status=cubierto}.Path) | cash | cubierto |
| Caja | POST | $(@{Domain=Caja; Method=POST; Path=/api/v1/pos/cash-shifts/{cash_shift_id}/close; FrontendArea=cash; Status=parcial / revisar uso exacto}.Path) | cash | parcial / revisar uso exacto |
| Caja | GET | $(@{Domain=Caja; Method=GET; Path=/api/v1/pos/cash-shifts/{cash_shift_id}/summary; FrontendArea=cash; Status=parcial / revisar uso exacto}.Path) | cash | parcial / revisar uso exacto |
| Caja | GET | $(@{Domain=Caja; Method=GET; Path=/api/v1/pos/cash-shifts/current; FrontendArea=cash; Status=cubierto}.Path) | cash | cubierto |
| Caja | POST | $(@{Domain=Caja; Method=POST; Path=/api/v1/pos/cash-shifts/open; FrontendArea=cash; Status=cubierto}.Path) | cash | cubierto |
| Catalogo | GET | $(@{Domain=Catalogo; Method=GET; Path=/api/v1/catalog/categories; FrontendArea=products / commands / payments / production; Status=cubierto}.Path) | products / commands / payments / production | cubierto |
| Catalogo | GET | $(@{Domain=Catalogo; Method=GET; Path=/api/v1/catalog/products; FrontendArea=products / commands / payments / production; Status=cubierto}.Path) | products / commands / payments / production | cubierto |
| Catalogo | GET | $(@{Domain=Catalogo; Method=GET; Path=/api/v1/catalog/stations; FrontendArea=products / commands / payments / production; Status=cubierto}.Path) | products / commands / payments / production | cubierto |
| Catalogo | GET | $(@{Domain=Catalogo; Method=GET; Path=/api/v1/production/station-orders; FrontendArea=products / commands / payments / production; Status=cubierto}.Path) | products / commands / payments / production | cubierto |
| Catalogo | POST | $(@{Domain=Catalogo; Method=POST; Path=/api/v1/production/station-orders/{station_order_id}/complete; FrontendArea=products / commands / payments / production; Status=parcial / revisar uso exacto}.Path) | products / commands / payments / production | parcial / revisar uso exacto |
| Catalogo | POST | $(@{Domain=Catalogo; Method=POST; Path=/api/v1/production/station-orders/{station_order_id}/deliver; FrontendArea=products / commands / payments / production; Status=parcial / revisar uso exacto}.Path) | products / commands / payments / production | parcial / revisar uso exacto |
| Catalogo | POST | $(@{Domain=Catalogo; Method=POST; Path=/api/v1/production/station-orders/{station_order_id}/receive; FrontendArea=products / commands / payments / production; Status=parcial / revisar uso exacto}.Path) | products / commands / payments / production | parcial / revisar uso exacto |
| Catalogo | POST | $(@{Domain=Catalogo; Method=POST; Path=/api/v1/production/station-orders/{station_order_id}/start; FrontendArea=products / commands / payments / production; Status=parcial / revisar uso exacto}.Path) | products / commands / payments / production | parcial / revisar uso exacto |
| Catalogo | GET | $(@{Domain=Catalogo; Method=GET; Path=/api/v1/reports/production-times; FrontendArea=products / commands / payments / production; Status=cubierto}.Path) | products / commands / payments / production | cubierto |
| Catalogo | GET | $(@{Domain=Catalogo; Method=GET; Path=/api/v1/reports/sales-by-product; FrontendArea=products / commands / payments / production; Status=cubierto}.Path) | products / commands / payments / production | cubierto |
| Impresion | GET | $(@{Domain=Impresion; Method=GET; Path=/api/v1/pos/print-jobs/pending; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | GET | $(@{Domain=Impresion; Method=GET; Path=/api/v1/printing/jobs/{print_job_id}; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | POST | $(@{Domain=Impresion; Method=POST; Path=/api/v1/printing/jobs/{print_job_id}/failed; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | POST | $(@{Domain=Impresion; Method=POST; Path=/api/v1/printing/jobs/{print_job_id}/printed; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | POST | $(@{Domain=Impresion; Method=POST; Path=/api/v1/printing/jobs/{print_job_id}/reprint; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | POST | $(@{Domain=Impresion; Method=POST; Path=/api/v1/printing/jobs/claim-next; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | GET | $(@{Domain=Impresion; Method=GET; Path=/api/v1/printing/jobs/pending; FrontendArea=printing; Status=cubierto}.Path) | printing | cubierto |
| Impresion | POST | $(@{Domain=Impresion; Method=POST; Path=/api/v1/printing/jobs/retry-failed; FrontendArea=printing; Status=cubierto}.Path) | printing | cubierto |
| Impresion | GET | $(@{Domain=Impresion; Method=GET; Path=/api/v1/printing/printers; FrontendArea=printing; Status=parcial / revisar uso exacto}.Path) | printing | parcial / revisar uso exacto |
| Impresion | GET | $(@{Domain=Impresion; Method=GET; Path=/api/v1/reports/print-jobs-summary; FrontendArea=printing; Status=cubierto}.Path) | printing | cubierto |
| Inventario y compras | GET | $(@{Domain=Inventario y compras; Method=GET; Path=/api/v1/inventory/items; FrontendArea=inventory; Status=cubierto}.Path) | inventory | cubierto |
| Inventario y compras | GET | $(@{Domain=Inventario y compras; Method=GET; Path=/api/v1/inventory/items/{inventory_item_id}/stock; FrontendArea=inventory; Status=parcial / revisar uso exacto}.Path) | inventory | parcial / revisar uso exacto |
| Inventario y compras | POST | $(@{Domain=Inventario y compras; Method=POST; Path=/api/v1/inventory/movements; FrontendArea=inventory; Status=cubierto}.Path) | inventory | cubierto |
| Inventario y compras | POST | $(@{Domain=Inventario y compras; Method=POST; Path=/api/v1/inventory/purchase-receipts; FrontendArea=inventory; Status=cubierto}.Path) | inventory | cubierto |
| Inventario y compras | GET | $(@{Domain=Inventario y compras; Method=GET; Path=/api/v1/inventory/stock-alerts/active; FrontendArea=inventory; Status=cubierto}.Path) | inventory | cubierto |
| Inventario y compras | GET | $(@{Domain=Inventario y compras; Method=GET; Path=/api/v1/reports/inventory-consumption; FrontendArea=inventory; Status=cubierto}.Path) | inventory | cubierto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/audit/tickets/{ticket_id}; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/catalog/payment-methods; FrontendArea=payments; Status=cubierto}.Path) | payments | cubierto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/catalog/products/{product_id}/variant-groups; FrontendArea=variants; Status=parcial / revisar uso exacto}.Path) | variants | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/catalog/variant-groups; FrontendArea=variants; Status=parcial / revisar uso exacto}.Path) | variants | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/operations/tables; FrontendArea=tables; Status=cubierto}.Path) | tables | cubierto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tables/{table_id}/open-ticket; FrontendArea=tables; Status=parcial / revisar uso exacto}.Path) | tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/ticket-lines/{line_id}/cancel; FrontendArea=ticket-cancel / ticket-adjustments; Status=parcial / revisar uso exacto}.Path) | ticket-cancel / ticket-adjustments | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/ticket-lines/{line_id}/modify; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/cancel; FrontendArea=ticket-cancel / ticket-adjustments; Status=parcial / revisar uso exacto}.Path) | ticket-cancel / ticket-adjustments | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}/discounts; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/discounts; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}/inventory-movements; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}/lines; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/lines; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}/payments; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/payments; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/send-round; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}/splits; FrontendArea=ticket-split; Status=parcial / revisar uso exacto}.Path) | ticket-split | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/splits/by-lines; FrontendArea=ticket-split; Status=parcial / revisar uso exacto}.Path) | ticket-split | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/splits/equal; FrontendArea=ticket-split; Status=parcial / revisar uso exacto}.Path) | ticket-split | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/tickets/{ticket_id}/start-payment; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/pos/tickets/{ticket_id}/station-orders; FrontendArea=tickets / tables; Status=parcial / revisar uso exacto}.Path) | tickets / tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/pos/ticket-splits/{split_id}/payments; FrontendArea=ticket-split; Status=parcial / revisar uso exacto}.Path) | ticket-split | parcial / revisar uso exacto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/reports/sales-by-payment-method; FrontendArea=payments; Status=cubierto}.Path) | payments | cubierto |
| POS | GET | $(@{Domain=POS; Method=GET; Path=/api/v1/system/airtable-sync; FrontendArea=tables; Status=cubierto}.Path) | tables | cubierto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/system/airtable-sync/pull; FrontendArea=tables; Status=parcial / revisar uso exacto}.Path) | tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/system/airtable-sync/push; FrontendArea=tables; Status=parcial / revisar uso exacto}.Path) | tables | parcial / revisar uso exacto |
| POS | POST | $(@{Domain=POS; Method=POST; Path=/api/v1/system/airtable-sync/run; FrontendArea=tables; Status=cubierto}.Path) | tables | cubierto |
| Preflight / notificaciones | GET | $(@{Domain=Preflight / notificaciones; Method=GET; Path=/api/v1/notifications/sms; FrontendArea=no aplica operador o pendiente admin; Status=no aplica frontend}.Path) | no aplica operador o pendiente admin | no aplica frontend |
| Preflight / notificaciones | POST | $(@{Domain=Preflight / notificaciones; Method=POST; Path=/api/v1/notifications/sms/test; FrontendArea=no aplica operador o pendiente admin; Status=no aplica frontend}.Path) | no aplica operador o pendiente admin | no aplica frontend |
| Preflight / notificaciones | GET | $(@{Domain=Preflight / notificaciones; Method=GET; Path=/api/v1/preflight/local-backend; FrontendArea=no aplica operador o pendiente admin; Status=no aplica frontend}.Path) | no aplica operador o pendiente admin | no aplica frontend |
| Reportes y auditoria | GET | $(@{Domain=Reportes y auditoria; Method=GET; Path=/api/v1/audit/events; FrontendArea=audit; Status=cubierto}.Path) | audit | cubierto |
| Reportes y auditoria | GET | $(@{Domain=Reportes y auditoria; Method=GET; Path=/api/v1/reports/operational-summary; FrontendArea=reports; Status=cubierto}.Path) | reports | cubierto |
| Seguridad | POST | $(@{Domain=Seguridad; Method=POST; Path=/api/v1/auth/login-pin; FrontendArea=auth; Status=cubierto}.Path) | auth | cubierto |
| Seguridad | POST | $(@{Domain=Seguridad; Method=POST; Path=/api/v1/auth/logout; FrontendArea=auth; Status=cubierto}.Path) | auth | cubierto |
| Seguridad | GET | $(@{Domain=Seguridad; Method=GET; Path=/api/v1/auth/me; FrontendArea=auth; Status=cubierto}.Path) | auth | cubierto |
| Seguridad | GET | $(@{Domain=Seguridad; Method=GET; Path=/api/v1/operations/employees; FrontendArea=security / auth; Status=cubierto}.Path) | security / auth | cubierto |
| Sistema y sincronizacion | GET | $(@{Domain=Sistema y sincronizacion; Method=GET; Path=/api/v1/system/business-settings; FrontendArea=system; Status=parcial / revisar uso exacto}.Path) | system | parcial / revisar uso exacto |
| Sistema y sincronizacion | GET | $(@{Domain=Sistema y sincronizacion; Method=GET; Path=/api/v1/system/db; FrontendArea=system; Status=parcial / revisar uso exacto}.Path) | system | parcial / revisar uso exacto |
| Sistema y sincronizacion | GET | $(@{Domain=Sistema y sincronizacion; Method=GET; Path=/api/v1/system/seed-summary; FrontendArea=system; Status=parcial / revisar uso exacto}.Path) | system | parcial / revisar uso exacto |
| Sistema y sincronizacion | GET | $(@{Domain=Sistema y sincronizacion; Method=GET; Path=/health; FrontendArea=system; Status=cubierto}.Path) | system | cubierto |
Placeholders / módulos en preparación detectados

- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=19; Line=import { ComingSoonPage } from "../shared/components/ComingSoonPage";}.Path):19 import { ComingSoonPage } from "../shared/components/ComingSoonPage";
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=25; Line=function ModulePlaceholder({ item }: { item: NavigationItem }) {}.Path):25 function ModulePlaceholder({ item }: { item: NavigationItem }) {
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=26; Line=  const page = <ComingSoonPage title={item.label} />;}.Path):26 const page = <ComingSoonPage title={item.label} />;
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=27; Line=  if (item.status === "coming_soon") return page;}.Path):27 if (item.status === "coming_soon") return page;
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=110; Line=                  element={<ModulePlaceholder item={item} />}}.Path):110 element={<ModulePlaceholder item={item} />}
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\layouts\AppShell.tsx; LineNumber=53; Line=      {access === "coming_soon" ? <span className="text-[10px]">Próximo</span> : null}}.Path):53 {access === "coming_soon" ? <span className="text-[10px]">Próximo</span> : null}
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\layouts\navigationItems.ts; LineNumber=25; Line=  status: "available" | "coming_soon";}.Path):25 status: "available" | "coming_soon";
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\layouts\navigationItems.ts; LineNumber=31; Line=export type NavigationItemAccess = "available" | "coming_soon" | "denied";}.Path):31 export type NavigationItemAccess = "available" | "coming_soon" | "denied";
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\layouts\navigationItems.ts; LineNumber=67; Line=  if (item.status === "coming_soon") return "coming_soon";}.Path):67 if (item.status === "coming_soon") return "coming_soon";

Posibles textos técnicos visibles detectados

Revisar manualmente. Algunos hallazgos pueden ser variables internas, no texto visible.

- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=2; Line=import { HashRouter, Navigate, Outlet, Route, Routes } from "react-router";}.Path):2 import { HashRouter, Navigate, Outlet, Route, Routes } from "react-router";
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=69; Line=    <HashRouter>}.Path):69 <HashRouter>
- $(@{Path=C:\Users\cuauh\Desktop\kanpai-pos\frontend\src\app\router.tsx; LineNumber=117; Line=    </HashRouter>}.Path):117 </HashRouter>

Query keys
export const queryKeys = {
  auth: {
    me: ["auth", "me"] as const,
  },
  cash: {
    current: ["cash", "current"] as const,
    summary: (cashShiftId: number) => ["cash", "summary", cashShiftId] as const,
  },
  checkout: {
    current: (ticketId: number) => ["checkout", "current", ticketId] as const,
  },
  catalog: {
    categories: ["catalog", "categories"] as const,
    paymentMethods: ["catalog", "payment-methods"] as const,
    products: ["catalog", "products"] as const,
    stations: ["catalog", "stations"] as const,
    productVariantGroups: (productId: number) =>
      ["catalog", "product-variant-groups", productId] as const,
  },
  commands: {
    stationOrders: (ticketId: number) =>
      ["commands", "station-orders", ticketId] as const,
  },
  discounts: {
    ticket: (ticketId: number) => ["discounts", "ticket", ticketId] as const,
  },
  payments: {
    list: (ticketId: number) => ["payments", "list", ticketId] as const,
  },
  production: {
    stations: ["production", "stations"] as const,
    orders: (stationId?: number) =>
      ["production", "orders", stationId ?? "all"] as const,
  },
  printing: {
    jobs: ["printing", "jobs"] as const,
  },
  reports: {
    dailySales: ["reports", "daily-sales"] as const,
    inventoryConsumption: ["reports", "inventory-consumption"] as const,
    salesByProduct: ["reports", "sales-by-product"] as const,
    salesByPaymentMethod: ["reports", "sales-by-payment-method"] as const,
    productionTimes: ["reports", "production-times"] as const,
    printJobs: ["reports", "print-jobs"] as const,
  },
  audit: {
    events: ["audit", "events"] as const,
    ticket: (ticketId: number) => ["audit", "ticket", ticketId] as const,
    cashShift: (cashShiftId: number) => ["audit", "cash-shift", cashShiftId] as const,
  },
  tables: {
    list: ["tables", "list"] as const,
  },
  tickets: {
    detail: (ticketId: number) => ["tickets", "detail", ticketId] as const,
    lines: (ticketId: number) => ["tickets", "lines", ticketId] as const,
    splits: (ticketId: number) => ["tickets", "splits", ticketId] as const,
  },
  inventory: {
    items: ["inventory", "items"] as const,
    stockAlerts: ["inventory", "stock-alerts"] as const,
  },
  security: {
    employees: ["security", "employees"] as const,
  },
  system: {
    health: ["system", "health"] as const,
    airtableSyncStatus: ["system", "airtable-sync-status"] as const,
  },
};

Build output
$ tsc && vite build
Diff check output

Criterio de cierre

El frontend queda listo para pasar a pruebas SQLite ↔ Airtable solo si:

No hay endpoints transaccionales pendientes sin UI ni documento de brecha.
El build pasa.
git diff --check no muestra errores reales.
Las brechas restantes son falta de contrato backend, no falta de frontend.
QA mutante POS queda explícitamente separado de pruebas de sincronización.

