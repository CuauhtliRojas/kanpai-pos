import type { AuditEvent } from "../types/auditTypes";

export type AuditCategory = "Caja" | "Cuenta" | "Producto/venta" | "Producción" | "Impresión" | "Inventario" | "Seguridad" | "Sistema";
export type AuditSeverity = "neutral" | "warning" | "danger" | "success";

const titleFixes: Record<string, string> = {
  "Corte abierto": "Corte abierto",
  "Corte cerrado": "Corte cerrado",
  "Gasto de caja creado": "Gasto de caja creado",
  "Ticket abierto": "Ticket abierto",
  "Linea de ticket agregada": "Línea de ticket agregada",
  "Paquete agregado": "Paquete agregado",
  "Ronda enviada": "Ronda enviada",
  "Cobro iniciado": "Cobro iniciado",
  "Pago creado": "Pago creado",
  "Pago registrado": "Pago registrado",
  "Ticket cobrado": "Ticket cobrado",
  "Linea de ticket cancelada": "Línea de ticket cancelada",
  "Ticket cancelado": "Ticket cancelado",
  "Movimiento de inventario creado": "Movimiento de inventario creado",
  "Recepcion procesada": "Recepción procesada",
  "Alerta de stock abierta": "Alerta de stock abierta",
  "Alerta de stock resuelta": "Alerta de stock resuelta",
  "Orden de produccion recibida": "Orden de producción recibida",
  "Orden de produccion iniciada": "Orden de producción iniciada",
  "Orden de produccion terminada": "Orden de producción terminada",
  "Orden de produccion entregada": "Orden de producción entregada",
  "Modificacion de linea": "Modificación de línea",
  "Descuento aplicado": "Descuento aplicado",
  "Cortesia aplicada": "Cortesía aplicada",
  "Reimpresion solicitada": "Reimpresión solicitada",
  "Division de cuenta creada": "División de cuenta creada",
  "Pago de division registrado": "Pago de división registrado",
  "Divisiones de ticket canceladas": "Divisiones de ticket canceladas",
  "Notificacion SMS fallida": "Notificación SMS fallida",
};

const entityLabels: Record<string, string> = {
  CashExpense: "Gasto",
  CashShift: "Corte",
  InventoryMovement: "Inventario",
  Payment: "Pago",
  PrintJob: "Impresión",
  PurchaseReceipt: "Recepción",
  StationOrder: "Comanda",
  StockAlert: "Alerta de stock",
  Ticket: "Ticket",
  TicketLine: "Producto",
  TicketLineModification: "Modificación",
  TicketSplit: "División",
};

export function formatAuditEventTitle(eventType: string): string {
  if (titleFixes[eventType]) return titleFixes[eventType];
  if (!eventType.includes("_")) return eventType.charAt(0).toUpperCase() + eventType.slice(1);

  const lower = eventType.toLowerCase().replace(/_/g, " ");
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

export function getAuditCategory(event: AuditEvent): AuditCategory {
  const text = `${event.entity_type} ${event.event_type}`.toLowerCase();
  if (text.includes("cash") || text.includes("corte") || text.includes("gasto")) return "Caja";
  if (text.includes("print") || text.includes("impresi") || text.includes("reimpresi")) return "Impresión";
  if (text.includes("inventory") || text.includes("inventario") || text.includes("stock") || text.includes("recepci")) return "Inventario";
  if (text.includes("station") || text.includes("production") || text.includes("comanda") || text.includes("producci") || text.includes("ronda")) return "Producción";
  if (text.includes("sms") || text.includes("session") || text.includes("seguridad")) return "Seguridad";
  if (text.includes("ticketline") || text.includes("producto") || text.includes("paquete") || text.includes("descuento") || text.includes("cortes")) return "Producto/venta";
  if (text.includes("ticket") || text.includes("payment") || text.includes("pago") || text.includes("cobro") || text.includes("cuenta")) return "Cuenta";
  return "Sistema";
}

export function formatEntityLabel(event: AuditEvent): string {
  const label = entityLabels[event.entity_type] ?? event.entity_type;
  return `${label} #${event.entity_id}`;
}

export function getAuditSeverity(event: AuditEvent): AuditSeverity {
  const text = `${event.event_type} ${event.reason ?? ""}`.toLowerCase();
  if (text.includes("cancel") || text.includes("fallid") || text.includes("failed")) return "danger";
  if (text.includes("alerta") || text.includes("modific") || text.includes("descuento") || text.includes("cortesía") || text.includes("cortesia")) return "warning";
  if (text.includes("cobrado") || text.includes("cerrado") || text.includes("terminada") || text.includes("entregada") || text.includes("resuelta")) return "success";
  return "neutral";
}

export function getAuditDetailTarget(event: AuditEvent): { ticketId: number | null; cashShiftId: number | null } | null {
  if (event.ticket_id !== null) return { ticketId: event.ticket_id, cashShiftId: null };
  if (event.cash_shift_id !== null) return { ticketId: null, cashShiftId: event.cash_shift_id };
  if (event.entity_type === "Ticket") return { ticketId: event.entity_id, cashShiftId: null };
  if (event.entity_type === "CashShift") return { ticketId: null, cashShiftId: event.entity_id };
  return null;
}
