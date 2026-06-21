import type { DiningTable } from "../types/tableTypes";
import { TableCard } from "./TableCard";

type TableGridProps = {
  tables: DiningTable[];
  selectedTableId: number | null;
  onSelect: (table: DiningTable) => void;
};

export function TableGrid({ tables, selectedTableId, onSelect }: TableGridProps) {
  if (tables.length === 0) {
    return (
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-6 text-center text-2xl font-black uppercase shadow-[var(--kp-shadow-hard)]">
        Sin mesas
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
      {tables.map((table) => (
        <TableCard
          key={table.id}
          table={table}
          selected={table.id === selectedTableId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
