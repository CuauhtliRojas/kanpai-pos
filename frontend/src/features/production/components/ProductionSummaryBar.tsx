import type { ProductionOrder } from "../types/productionTypes";
import { getProductionSummary, type ProductionViewFilter } from "../productionFormatters";

type ProductionSummaryBarProps = {
  orders: ProductionOrder[];
  activeFilter?: ProductionViewFilter;
  onFilterSelect?: (filter: ProductionViewFilter) => void;
};

const summaryItems = [
  {
    key: "waiting",
    label: "Por recibir",
    filter: "active",
    className: "bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  },
  {
    key: "preparing",
    label: "Preparando",
    filter: "active",
    className: "bg-[var(--kp-info)] text-[var(--kp-info-contrast)]",
  },
  {
    key: "ready",
    label: "Listas",
    filter: "ready",
    className: "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
  },
  {
    key: "delivered",
    label: "Entregadas",
    filter: "delivered",
    className: "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
  },
] as const;

export function ProductionSummaryBar({ orders, onFilterSelect }: ProductionSummaryBarProps) {
  const summary = getProductionSummary(orders);

  return (
    <section className="grid grid-cols-2 gap-3 md:grid-cols-4" aria-label="Resumen de comandas">
      {summaryItems.map((item) => {
        const className = [
          "border-4 border-[var(--kp-ink)] p-3 text-left shadow-[var(--kp-shadow-hard-sm)] transition",
          "focus-visible:outline-none focus-visible:ring-0",
          item.className,
        ].join(" ");

        if (onFilterSelect) {
          return (
            <button
              key={item.key}
              type="button"
              onClick={() => onFilterSelect(item.filter)}
              className={`${className} active:translate-x-[3px] active:translate-y-[3px] active:shadow-none`}
            >
              <p className="text-3xl font-black leading-none">{summary[item.key]}</p>
              <p className="mt-1 text-xs font-black uppercase tracking-[0.08em]">{item.label}</p>
            </button>
          );
        }

        return (
          <div key={item.key} className={className}>
            <p className="text-3xl font-black leading-none">{summary[item.key]}</p>
            <p className="mt-1 text-xs font-black uppercase tracking-[0.08em]">{item.label}</p>
          </div>
        );
      })}
    </section>
  );
}
