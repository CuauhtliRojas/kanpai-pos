import type { ProductionOrder, ProductionOrderStatus } from "./types/productionTypes";

export type ProductionViewFilter = "active" | "ready" | "delivered" | "all";

export const productionViewFilters: Array<{
  value: ProductionViewFilter;
  label: string;
}> = [
  { value: "active", label: "Activas" },
  { value: "ready", label: "Listas" },
  { value: "delivered", label: "Entregadas" },
  { value: "all", label: "Todas" },
];

export const statusPriority: Record<ProductionOrderStatus, number> = {
  "En cola": 1,
  Recibida: 2,
  "En preparacion": 3,
  Terminada: 4,
  Entregada: 5,
  Cancelada: 6,
};

export const statusPresentation = {
  "En cola": { label: "Por recibir", tone: "warning" },
  Recibida: { label: "Recibida", tone: "info" },
  "En preparacion": { label: "Preparando", tone: "warning" },
  Terminada: { label: "Lista", tone: "ok" },
  Entregada: { label: "Entregada", tone: "neutral" },
  Cancelada: { label: "Cancelada", tone: "danger" },
} as const;

export function getOrderStateTimestamp(order: ProductionOrder): string {
  if (order.status === "Entregada") return order.delivered_at ?? order.created_at;
  if (order.status === "Terminada") return order.completed_at ?? order.created_at;
  if (order.status === "En preparacion") return order.started_at ?? order.created_at;
  if (order.status === "Recibida") return order.received_at ?? order.created_at;
  return order.created_at;
}

function getTimeValue(value: string): number {
  const date = new Date(value);
  const time = date.getTime();
  return Number.isNaN(time) ? 0 : time;
}

export function getProductionTimeValue(value: string): number {
  return getTimeValue(value);
}

export function sortProductionOrders(orders: ProductionOrder[]): ProductionOrder[] {
  return [...orders].sort((left, right) => {
    const statusDelta = statusPriority[left.status] - statusPriority[right.status];
    if (statusDelta !== 0) return statusDelta;
    return getTimeValue(left.created_at) - getTimeValue(right.created_at);
  });
}

export function filterProductionOrders(
  orders: ProductionOrder[],
  filter: ProductionViewFilter,
): ProductionOrder[] {
  if (filter === "active") {
    return orders.filter((order) =>
      ["En cola", "Recibida", "En preparacion"].includes(order.status),
    );
  }
  if (filter === "ready") {
    return orders.filter((order) => order.status === "Terminada");
  }
  if (filter === "delivered") {
    return orders.filter((order) => order.status === "Entregada");
  }
  return orders;
}

export function getProductionSummary(orders: ProductionOrder[]) {
  return {
    waiting: orders.filter((order) => order.status === "En cola").length,
    preparing: orders.filter((order) =>
      order.status === "Recibida" || order.status === "En preparacion",
    ).length,
    ready: orders.filter((order) => order.status === "Terminada").length,
    delivered: orders.filter((order) => order.status === "Entregada").length,
  };
}

export function getEmptyProductionMessage(filter: ProductionViewFilter): {
  title: string;
  message?: string;
} {
  if (filter === "active") {
    return {
      title: "Sin comandas activas",
      message: "Cuando envíes una ronda aparecerá aquí.",
    };
  }
  if (filter === "ready") return { title: "Sin comandas listas" };
  if (filter === "delivered") return { title: "Sin comandas entregadas" };
  return { title: "Sin comandas para esta estación" };
}

export type ProductionAccountOrderGroup = {
  ticketId: number;
  orders: ProductionOrder[];
  dominantStatus: ProductionOrderStatus;
  oldestTimestamp: string;
  totalQuantity: number;
  totalLines: number;
};

function getDominantStatus(orders: ProductionOrder[]): ProductionOrderStatus {
  return orders.reduce<ProductionOrderStatus>((dominantStatus, order) => {
    return statusPriority[order.status] < statusPriority[dominantStatus]
      ? order.status
      : dominantStatus;
  }, orders[0]?.status ?? "Cancelada");
}

function getOldestTimestamp(orders: ProductionOrder[]): string {
  return orders.reduce((oldestTimestamp, order) => {
    return getTimeValue(order.created_at) < getTimeValue(oldestTimestamp)
      ? order.created_at
      : oldestTimestamp;
  }, orders[0]?.created_at ?? "");
}

export function groupProductionOrdersByAccount(
  orders: ProductionOrder[],
): ProductionAccountOrderGroup[] {
  const groupedOrders = new Map<number, ProductionOrder[]>();

  orders.forEach((order) => {
    const accountOrders = groupedOrders.get(order.ticket_id) ?? [];
    accountOrders.push(order);
    groupedOrders.set(order.ticket_id, accountOrders);
  });

  return Array.from(groupedOrders.entries())
    .map(([ticketId, accountOrders]) => {
      const sortedOrders = sortProductionOrders(accountOrders);
      return {
        ticketId,
        orders: sortedOrders,
        dominantStatus: getDominantStatus(sortedOrders),
        oldestTimestamp: getOldestTimestamp(sortedOrders),
        totalQuantity: sortedOrders.reduce(
          (total, order) => total + order.lines.reduce((lineTotal, line) => lineTotal + line.quantity, 0),
          0,
        ),
        totalLines: sortedOrders.reduce((total, order) => total + order.lines.length, 0),
      };
    })
    .sort((left, right) => {
      const statusDelta = statusPriority[left.dominantStatus] - statusPriority[right.dominantStatus];
      if (statusDelta !== 0) return statusDelta;
      return getTimeValue(left.oldestTimestamp) - getTimeValue(right.oldestTimestamp);
    });
}

export function formatRelativeProductionTime(value: string): string {
  const time = getTimeValue(value);
  if (!time) return "Sin hora";

  const elapsedMs = Date.now() - time;
  if (elapsedMs < 60_000) return "Hace menos de 1 min";

  const elapsedMinutes = Math.max(1, Math.floor(elapsedMs / 60_000));
  if (elapsedMinutes < 60) return `Hace ${elapsedMinutes} min`;

  const elapsedHours = Math.floor(elapsedMinutes / 60);
  if (elapsedHours < 24) return `Hace ${elapsedHours} h`;

  const elapsedDays = Math.floor(elapsedHours / 24);
  return `Hace ${elapsedDays} d`;
}

export function formatProductionTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatProductionLastUpdated(value: Date | null): string {
  if (!value) return "Sin actualización";
  return new Intl.DateTimeFormat("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(value);
}
