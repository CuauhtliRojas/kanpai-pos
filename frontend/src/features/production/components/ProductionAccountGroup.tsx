import { StatusBadge } from "../../../shared/components/StatusBadge";
import {
  formatProductionTime,
  formatRelativeProductionTime,
  getOrderStateTimestamp,
  type ProductionAccountOrderGroup,
  statusPresentation,
} from "../productionFormatters";
import type { ProductionOrder } from "../types/productionTypes";
import { ProductionActionBar } from "./ProductionActionBar";
import { ProductionOrderLines } from "./ProductionOrderLines";

type ProductionAccountGroupProps = {
  group: ProductionAccountOrderGroup;
  expanded: boolean;
  activeOrderId: number | null;
  onToggle: (ticketId: number) => void;
  getErrorMessage: (order: ProductionOrder) => string | null;
  isOrderPending: (order: ProductionOrder) => boolean;
  onAccept: (order: ProductionOrder) => void;
  onStart: (order: ProductionOrder) => void;
  onFinish: (order: ProductionOrder) => void;
  onDeliver: (order: ProductionOrder) => void;
};

function formatCount(value: number, singular: string, plural: string): string {
  return `${value} ${value === 1 ? singular : plural}`;
}

function getTimestampItems(order: ProductionOrder) {
  return [
    { label: "Recibida", value: order.received_at },
    { label: "Iniciada", value: order.started_at },
    { label: "Lista", value: order.completed_at },
    { label: "Entregada", value: order.delivered_at },
  ].filter((item) => item.value);
}

export function ProductionAccountGroup({
  group,
  expanded,
  activeOrderId,
  onToggle,
  getErrorMessage,
  isOrderPending,
  onAccept,
  onStart,
  onFinish,
  onDeliver,
}: ProductionAccountGroupProps) {
  const groupStatus = statusPresentation[group.dominantStatus];

  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard)]">
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => onToggle(group.ticketId)}
        className="grid w-full gap-3 bg-[var(--kp-surface)] p-3 text-left transition active:translate-x-[3px] active:translate-y-[3px] sm:grid-cols-[1fr_auto] sm:items-center"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-black uppercase leading-none">Cuenta #{group.ticketId}</h2>
            <StatusBadge label={groupStatus.label} tone={groupStatus.tone} />
          </div>
          <p className="mt-2 text-sm font-bold text-[var(--kp-muted)]">
            {formatCount(group.orders.length, "comanda", "comandas")} ·{" "}
            {formatCount(group.totalQuantity, "producto", "productos")} ·{" "}
            {formatCount(group.totalLines, "línea", "líneas")}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-2 py-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-text-on-dark)]">
            {formatRelativeProductionTime(group.oldestTimestamp)}
          </span>
          <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            {expanded ? "Cerrar" : "Abrir"}
          </span>
        </div>
      </button>

      {expanded ? (
        <div className="grid gap-2 border-t-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-2">
          {group.orders.map((order) => {
            const orderStatus = statusPresentation[order.status];
            const productQuantity = order.lines.reduce((total, line) => total + line.quantity, 0);
            const errorMessage = activeOrderId === order.id ? getErrorMessage(order) : null;

            return (
              <article
                key={order.id}
                className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)]"
              >
                <div className="grid gap-3 lg:grid-cols-[1fr_11rem] lg:items-start">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge label={orderStatus.label} tone={orderStatus.tone} />
                      <h3 className="text-lg font-black uppercase leading-none">{order.folio}</h3>
                      <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-2 py-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-text-on-dark)]">
                        {formatRelativeProductionTime(getOrderStateTimestamp(order))}
                      </span>
                      <span className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
                        {formatCount(productQuantity, "producto", "productos")}
                      </span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {getTimestampItems(order).map((item) => (
                        <span
                          key={item.label}
                          className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1 text-[10px] font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]"
                        >
                          {item.label}: {formatProductionTime(item.value)}
                        </span>
                      ))}
                    </div>
                  </div>
                  <ProductionActionBar
                    status={order.status}
                    isPending={isOrderPending(order)}
                    compact
                    onAccept={() => onAccept(order)}
                    onStart={() => onStart(order)}
                    onFinish={() => onFinish(order)}
                    onDeliver={() => onDeliver(order)}
                  />
                </div>

                <ProductionOrderLines lines={order.lines} compact />

                {errorMessage ? (
                  <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
                    {errorMessage}
                  </p>
                ) : null}
              </article>
            );
          })}
        </div>
      ) : null}
    </section>
  );
}
