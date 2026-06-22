import type { DiningTable } from "../types/tableTypes";
import { TableCard } from "./TableCard";

type TableGridProps = {
  tables: DiningTable[];
  selectedTableId: number | null;
  compact?: boolean;
  onSelect: (table: DiningTable) => void;
  onViewSales?: (table: DiningTable) => void;
  historyTableIds?: Set<number>;
};

export function TableGrid({ tables, selectedTableId, compact = false, onSelect, onViewSales, historyTableIds }: TableGridProps) {
  if (tables.length === 0) {
    return (
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center shadow-[var(--kp-shadow-hard)]">
        <p className="text-2xl font-black uppercase">No hay mesas disponibles</p>
        <p className="mt-2 font-bold text-[var(--kp-muted)]">Intenta de nuevo en un momento.</p>
      </div>
    );
  }

  return (
    <div className={compact ? "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4" : "grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6"}>
      {tables.map((table) => (
        <TableCard
          key={table.id}
          table={table}
          selected={table.id === selectedTableId}
          compact={compact}
          onSelect={onSelect}
          onViewSales={historyTableIds?.has(table.id) ? onViewSales : undefined}
        />
      ))}
    </div>
  );
}
