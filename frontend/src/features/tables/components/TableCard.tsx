import { Armchair } from "lucide-react";
import type { DiningTable } from "../types/tableTypes";
import { TableStatusBadge } from "./TableStatusBadge";

type TableCardProps = {
  table: DiningTable;
  selected: boolean;
  onSelect: (table: DiningTable) => void;
};

export function TableCard({ table, selected, onSelect }: TableCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(table)}
      aria-pressed={selected}
      className={[
        "grid min-h-32 content-between gap-3 border-4 border-[var(--kp-ink)] p-3 text-left shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
        selected
          ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
          : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-2">
        <Armchair className="h-7 w-7 shrink-0" />
        <TableStatusBadge status={table.status} selected={selected} />
      </div>
      <div>
        <p className="text-xl font-black uppercase leading-tight">
          {table.display_name || table.table_code || `Mesa ${table.id}`}
        </p>
        {table.display_name !== table.table_code ? (
          <p className="mt-1 text-xs font-bold uppercase opacity-70">{table.table_code}</p>
        ) : null}
      </div>
    </button>
  );
}
