import { useEffect, useMemo, useState } from "react";
import {
  getEmptyProductionMessage,
  groupProductionOrdersByAccount,
  statusPriority,
  type ProductionViewFilter,
} from "../productionFormatters";
import type { ProductionOrder } from "../types/productionTypes";
import { ProductionAccountGroup } from "./ProductionAccountGroup";

type ProductionOrderListProps = {
  orders: ProductionOrder[];
  filter: ProductionViewFilter;
  stationId: number | undefined;
  activeOrderId: number | null;
  getErrorMessage: (order: ProductionOrder) => string | null;
  isOrderPending: (order: ProductionOrder) => boolean;
  onAccept: (order: ProductionOrder) => void;
  onStart: (order: ProductionOrder) => void;
  onFinish: (order: ProductionOrder) => void;
  onDeliver: (order: ProductionOrder) => void;
};

function getDefaultExpandedTicketIds(
  groups: ReturnType<typeof groupProductionOrdersByAccount>,
  filter: ProductionViewFilter,
): Set<number> {
  if (filter === "delivered") return new Set();
  if (filter === "active" && groups.length > 5) {
    return new Set(
      groups
        .filter((group) => statusPriority[group.dominantStatus] <= statusPriority.Recibida)
        .map((group) => group.ticketId),
    );
  }
  if (groups.length <= 5) return new Set(groups.map((group) => group.ticketId));
  return new Set();
}

export function ProductionOrderList({
  orders,
  filter,
  stationId,
  activeOrderId,
  getErrorMessage,
  isOrderPending,
  onAccept,
  onStart,
  onFinish,
  onDeliver,
}: ProductionOrderListProps) {
  const groups = useMemo(() => groupProductionOrdersByAccount(orders), [orders]);
  const [expandedTicketIds, setExpandedTicketIds] = useState<Set<number>>(new Set());
  const [defaultKey, setDefaultKey] = useState<string>("");

  useEffect(() => {
    const nextDefaultKey = `${stationId ?? "none"}:${filter}`;
    if (defaultKey === nextDefaultKey) return;
    if (groups.length === 0) {
      setExpandedTicketIds(new Set());
      return;
    }
    setExpandedTicketIds(getDefaultExpandedTicketIds(groups, filter));
    setDefaultKey(nextDefaultKey);
  }, [defaultKey, filter, groups, stationId]);

  function toggleGroup(ticketId: number) {
    setExpandedTicketIds((currentTicketIds) => {
      const nextTicketIds = new Set(currentTicketIds);
      if (nextTicketIds.has(ticketId)) {
        nextTicketIds.delete(ticketId);
      } else {
        nextTicketIds.add(ticketId);
      }
      return nextTicketIds;
    });
  }

  if (groups.length === 0) {
    const emptyState = getEmptyProductionMessage(filter);
    return (
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center shadow-[var(--kp-shadow-hard)]">
        <p className="text-xl font-black uppercase">{emptyState.title}</p>
        {emptyState.message ? (
          <p className="mt-2 font-bold text-[var(--kp-muted)]">{emptyState.message}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {groups.map((group) => (
        <ProductionAccountGroup
          key={group.ticketId}
          group={group}
          expanded={expandedTicketIds.has(group.ticketId)}
          activeOrderId={activeOrderId}
          onToggle={toggleGroup}
          isOrderPending={isOrderPending}
          getErrorMessage={getErrorMessage}
          onAccept={onAccept}
          onStart={onStart}
          onFinish={onFinish}
          onDeliver={onDeliver}
        />
      ))}
    </div>
  );
}
