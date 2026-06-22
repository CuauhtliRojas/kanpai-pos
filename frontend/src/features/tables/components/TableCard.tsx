import { Armchair } from "lucide-react";
import type { DiningTable } from "../types/tableTypes";
import { TableStatusBadge } from "./TableStatusBadge";

type TableCardProps = {
  table: DiningTable;
  selected: boolean;
  compact?: boolean;
  onSelect: (table: DiningTable) => void;
  onViewSales?: (table: DiningTable) => void;
};

export function TableCard({ table, selected, compact = false, onSelect, onViewSales }: TableCardProps) {
  return (
    <div
      className={[
        "grid content-between border-4 border-[var(--kp-ink)] text-left shadow-[var(--kp-shadow-hard-sm)]",
        compact ? "min-h-28" : "min-h-36",
        selected
          ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
          : "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
      ].join(" ")}
    >
      <button type="button" onClick={() => onSelect(table)} aria-pressed={selected} className={`grid flex-1 content-between gap-3 text-left transition active:translate-x-[2px] active:translate-y-[2px] ${compact ? "p-3" : "p-4"}`}>
        <div className="flex items-start justify-between gap-2"><Armchair className={compact ? "h-5 w-5 shrink-0" : "h-7 w-7 shrink-0"} /><TableStatusBadge status={table.status} selected={selected} /></div>
        <div><p className={`${compact ? "text-base" : "text-xl"} font-black uppercase leading-tight`}>{table.display_name || table.table_code || `Mesa ${table.id}`}</p>{table.display_name !== table.table_code ? <p className="mt-1 text-xs font-bold uppercase opacity-70">{table.table_code}</p> : null}</div>
      </button>
      {onViewSales ? <button type="button" onClick={() => onViewSales(table)} className="min-h-11 border-t-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-3 text-xs font-black uppercase text-[var(--kp-text)]">Ver ventas</button> : null}
    </div>
  );
}
