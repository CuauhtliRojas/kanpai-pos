import { StatusBadge } from "../../../shared/components/StatusBadge";
import {
  formatProductionTime,
  formatRelativeProductionTime,
  getOrderStateTimestamp,
  statusPresentation,
} from "../productionFormatters";
import type { ProductionOrder } from "../types/productionTypes";
import { ProductionActionBar } from "./ProductionActionBar";
import { ProductionOrderLines } from "./ProductionOrderLines";

const cardAccentClassName: Record<ProductionOrder["status"], string> = {
  "En cola": "border-l-[var(--kp-warning)]",
  Recibida: "border-l-[var(--kp-info)]",
  "En preparacion": "border-l-[var(--kp-warning)]",
  Terminada: "border-l-[var(--kp-success)]",
  Entregada: "border-l-[var(--kp-surface-soft)]",
  Cancelada: "border-l-[var(--kp-danger)]",
};

type ProductionOrderCardProps = {
  order: ProductionOrder;
  isPending: boolean;
  errorMessage: string | null;
  onAccept: () => void;
  onStart: () => void;
  onFinish: () => void;
  onDeliver: () => void;
};

export function ProductionOrderCard({
  order,
  isPending,
  errorMessage,
  onAccept,
  onStart,
  onFinish,
  onDeliver,
}: ProductionOrderCardProps) {
  const presentation = statusPresentation[order.status];
  const ageLabel = formatRelativeProductionTime(getOrderStateTimestamp(order));
  const timestamps = [
    { label: "Recibida", value: order.received_at },
    { label: "Iniciada", value: order.started_at },
    { label: "Lista", value: order.completed_at },
    { label: "Entregada", value: order.delivered_at },
  ].filter((item) => item.value);

  return (
    <article
      className={`grid gap-4 border-4 border-l-8 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)] ${cardAccentClassName[order.status]}`}
    >
      <header className="grid gap-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[0.16em] text-[var(--kp-muted)]">
              Cuenta #{order.ticket_id}
            </p>
            <h2 className="mt-1 truncate text-3xl font-black uppercase leading-none md:text-4xl">
              {order.folio}
            </h2>
          </div>
          <StatusBadge label={presentation.label} tone={presentation.tone} />
        </div>
        <div className="flex flex-wrap gap-2 text-xs font-black uppercase tracking-[0.08em]">
          <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-2 py-1 text-[var(--kp-text-on-dark)]">
            {ageLabel}
          </span>
          {timestamps.map((item) => (
            <span
              key={item.label}
              className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1 text-[var(--kp-muted)]"
            >
              {item.label}: {formatProductionTime(item.value)}
            </span>
          ))}
        </div>
      </header>

      <ProductionOrderLines lines={order.lines} />

      {errorMessage ? (
        <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">
          {errorMessage}
        </p>
      ) : null}

      <ProductionActionBar
        status={order.status}
        isPending={isPending}
        onAccept={onAccept}
        onStart={onStart}
        onFinish={onFinish}
        onDeliver={onDeliver}
      />
    </article>
  );
}
