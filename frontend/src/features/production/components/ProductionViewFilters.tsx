import type { ProductionViewFilter } from "../productionFormatters";
import { productionViewFilters } from "../productionFormatters";

type ProductionViewFiltersProps = {
  value: ProductionViewFilter;
  onChange: (value: ProductionViewFilter) => void;
};

export function ProductionViewFilters({ value, onChange }: ProductionViewFiltersProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1" aria-label="Filtros de vista">
      {productionViewFilters.map((filter) => {
        const selected = filter.value === value;
        return (
          <button
            key={filter.value}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(filter.value)}
            className={`min-h-[var(--kp-touch-md)] shrink-0 border-4 border-[var(--kp-ink)] px-4 text-sm font-black uppercase tracking-[0.08em] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none ${selected
              ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
              : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]"
            }`}
          >
            {filter.label}
          </button>
        );
      })}
    </div>
  );
}
