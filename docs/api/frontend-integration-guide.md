# Guía de integración frontend

## Integración Fase 3-M

El contrato backend está disponible, pero esta fase no implementa frontend. Cocina/barra debe consultar `/production/station-orders` y mostrar sólo la siguiente acción válida. Las modificaciones usan `/ticket-lines/{id}/modify`; una línea enviada genera el aviso lógico automáticamente.

Consultar `/system/business-settings` antes de presentar importes. Si `tax_included=true`, `tax_cents` es informativo y no debe sumarse otra vez. Los porcentajes usan bps (1000 = 10 %). Descuentos y reimpresiones siempre solicitan motivo y empleado autorizador.

```ts
type ProductionStatus = "En cola" | "Recibida" | "En preparacion" | "Terminada" | "Entregada" | "Cancelada";
type DiscountType = "Monto" | "Porcentaje" | "Cortesia";
```

Base local: `http://127.0.0.1:8011`. Consumir JSON con `Content-Type: application/json`. Los endpoints siguen en inglés; las claves JSON siguen en inglés; estados, tipos y métodos persistidos llegan y se envían en español legible, incluyendo espacios.

## Errores y estados

- `400`: payload semánticamente inválido; `403`: falta permiso; `404`: recurso inexistente; `409`: conflicto de estado; `422`: forma/tipo del payload inválido; `500`: fallo no controlado.
- Mostrar `detail` al operador cuando sea accionable: `const message = await response.json().then(x => x.detail)`.
- No convertir valores a mayúsculas ni sustituir espacios. Enviar exactamente `Ajuste entrada`, `Consumo venta`, `Ticket cobrado`, etc.
- `OK`, `WARNING` y `ERROR` de preflight son resultados técnicos no persistidos y deliberadamente se conservan.

## Flujo POS principal

1. `GET /api/v1/preflight/local-backend`; bloquear sólo `ERROR` y advertir `WARNING`.
2. `GET /api/v1/pos/cash-shifts/current`; si 404, `POST /api/v1/pos/cash-shifts/open`.
3. `GET /api/v1/operations/tables`; elegir una mesa `Libre`.
4. `POST /api/v1/pos/tables/{id}/open-ticket`.
5. `GET /api/v1/catalog/categories` y `/products`.
6. `POST /api/v1/pos/tickets/{id}/lines` por producto.
7. `POST /api/v1/pos/tickets/{id}/send-round`.
8. `POST /api/v1/pos/tickets/{id}/start-payment`; nunca hacerlo con líneas `Capturado`.
9. `GET /api/v1/catalog/payment-methods`.
10. `POST /api/v1/pos/tickets/{id}/payments`; repetir para pago parcial hasta `closed: true`.
11. Consultar `/api/v1/printing/jobs/pending` sin ocultar fallidos del monitor operativo.

```ts
const API = "http://127.0.0.1:8011";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail ?? `HTTP ${response.status}`);
  return body as T;
}

const ticket = await api<Ticket>("/api/v1/pos/tables/1/open-ticket", {
  method: "POST",
  body: JSON.stringify({ employee_id: 1, waiter_employee_id: 1, guest_count: 2 }),
});

await api(`/api/v1/pos/tickets/${ticket.id}/lines`, {
  method: "POST",
  body: JSON.stringify({ product_id: 1, employee_id: 1, quantity: 1, note: "Sin cebolla" }),
});

await api(`/api/v1/pos/tickets/${ticket.id}/send-round`, {
  method: "POST",
  body: JSON.stringify({ employee_id: 1 }),
});
```

## Cancelación

- Línea: `POST /api/v1/pos/ticket-lines/{line_id}/cancel` con `{"employee_id":1,"reason":"Error de captura"}`. Refrescar ticket, líneas y cola; puede crear `Cancelacion comanda`.
- Ticket: `POST /api/v1/pos/tickets/{ticket_id}/cancel` con motivo. Refrescar mesas; la respuesta indica `table_released`.
- La UI debe pedir confirmación y motivo, mostrar 403 por permiso y no ofrecer cancelar un ticket `Cobrado`.

## Daemon de impresión

1. Polling `GET /api/v1/printing/jobs/pending?printer_key=COCINA`.
2. `POST /api/v1/printing/jobs/claim-next` con worker e impresora.
3. Si se imprimió, `POST /api/v1/printing/jobs/{id}/printed`.
4. Si falló, `POST /api/v1/printing/jobs/{id}/failed` con error y espera.
5. Periódicamente `POST /api/v1/printing/jobs/retry-failed`.

No hay impresión física en este backend: el daemon externo interpreta `content_snapshot`. No tratar `Tomado` como impreso. Mantener visibles `Fallido`, `last_error`, intentos y reintento.

## Inventario

```ts
await api("/api/v1/inventory/movements", {
  method: "POST",
  body: JSON.stringify({
    inventory_item_id: 1,
    movement_type: "Ajuste entrada",
    quantity_base: "500",
    employee_id: 1,
    reason: "Conteo físico",
  }),
});
```

Listar `/inventory/items`, consultar `/items/{id}/stock`, procesar `/purchase-receipts` y mantener un indicador para `/stock-alerts/active`. Una recepción usa estado final `Procesada`; una alerta activa usa `Abierta`.

## Reportes y auditoría

Usar rangos ISO locales en `/reports/*`. Para drill-down usar `/audit/tickets/{id}` y `/audit/cash-shifts/{id}`. El filtro `event_type` recibe el valor español exacto, por ejemplo `Ticket cobrado` URL-encoded, no `TICKET_PAID`.

## Tipos TypeScript sugeridos

```ts
type TicketStatus = "Abierto" | "En cobro" | "Cobrado" | "Cancelado";
type TicketPaymentStatus = "Sin pagar" | "Pagado" | "Cancelado";
type TicketLineStatus = "Capturado" | "Enviado a comanda" | "Impreso" | "Cancelado";
type TicketLineType = "Simple" | "Paquete padre" | "Componente de paquete";
type PrintStatus = "Pendiente" | "Tomado" | "Impreso" | "Fallido" | "Cancelado";
type PrintJobType = "Comanda" | "Ticket" | "Corte" | "Cancelacion comanda";
type PaymentMethod = "Efectivo" | "Tarjeta" | "Transferencia";
type MovementType = "Compra" | "Ajuste entrada" | "Ajuste salida" | "Merma" | "Consumo venta";
type StockStatus = "Correcto" | "Stock bajo" | "Sin stock";

interface Ticket {
  id: number;
  folio: string;
  status: TicketStatus;
  payment_status: TicketPaymentStatus;
  total_cents: number;
  table_id: number;
}

interface AddLinePayload { product_id: number; employee_id: number; quantity: number; note?: string }
interface PaymentPayload {
  employee_id: number;
  payment_method_id: number;
  amount_cents: number;
  received_cents?: number;
  reference?: string;
}
```

## Reglas de UI

- No permitir cobrar si existe una línea `Capturado`; ofrecer “Enviar ronda”.
- No permitir cerrar corte con tickets `Abierto` o `En cobro`.
- Mostrar advertencias cuando preflight sea `WARNING` y bloquear ante `ERROR`.
- No ocultar trabajos `Fallido`; ofrecer detalle y reintento.
- Usar centavos enteros para dinero y strings decimales para cantidades de inventario.
- No inferir cierre por monto en cliente: usar `closed` y estado devueltos por backend.
# Identidad y nuevas operaciones (Fase 3-N)

El frontend inicia sesión por PIN, conserva el token durante la sesión y usa `/auth/me` para resolver `employee.id`. Hasta activar middleware global, debe seguir enviando ese `employee_id` en captura, cobro y autorizaciones. No debe guardar ni registrar el PIN.

Para productos armables, consulte grupos antes de agregar la línea y respete mínimos/máximos. Para cobro dividido, refresque `GET /splits` después de cada pago. El frontend nunca llama impresoras Windows: solo muestra estado de la cola del backend.
