import type { ProductionStation } from "../types/productionTypes";

type ProductionStationTabsProps = {
  stations: ProductionStation[];
  selectedStationId: number | undefined;
  onSelect: (stationId: number) => void;
};

export function ProductionStationTabs({
  stations,
  selectedStationId,
  onSelect,
}: ProductionStationTabsProps) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-1" aria-label="Estaciones">
      {stations.map((station) => {
        const selected = station.id === selectedStationId;
        return (
          <button
            key={station.id}
            type="button"
            aria-pressed={selected}
            onClick={() => onSelect(station.id)}
            className={`min-h-[var(--kp-touch-md)] shrink-0 border-4 border-[var(--kp-ink)] px-5 text-sm font-black uppercase tracking-[0.08em] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none ${
              selected
                ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
                : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]"
            }`}
          >
            {station.name}
          </button>
        );
      })}
    </div>
  );
}
