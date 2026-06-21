import { StatusBadge } from "../../../shared/components/StatusBadge";
import type { ProductionOrder } from "../types/productionTypes";
import { ProductionActionBar } from "./ProductionActionBar";
import { ProductionOrderLines } from "./ProductionOrderLines";

const statusPresentation = {
  "En cola": { label: "Pendiente", tone: "warning" },
  Recibida: { label: "Aceptada", tone: "info" },
  "En preparacion": { label: "En preparación", tone: "info" },
  Terminada: { label: "Terminada", tone: "ok" },
  Entregada: { label: "Entregada", tone: "ok" },
  Cancelada: { label: "Cancelada", tone: "danger" },
} as const;

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
  return (
    <article className="grid min-h-72 gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <header className="flex items-start justify-between gap-3">
        <h2 className="text-2xl font-black uppercase">{order.folio}</h2>
        <StatusBadge label={presentation.label} tone={presentation.tone} />
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
