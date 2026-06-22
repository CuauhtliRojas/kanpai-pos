import { Search } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";

type Props = {
  query: string;
  status: string | undefined;
  tableId: number | undefined;
  currentTableId: number | null;
  onQueryChange: (value: string) => void;
  onStatusChange: (value: string | undefined) => void;
  onTableChange: (value: number | undefined) => void;
};

export function TicketHistorySearch({
  query,
  status,
  tableId,
  currentTableId,
  onQueryChange,
  onStatusChange,
  onTableChange,
}: Props) {
  return (
    <div className="grid gap-3">
      <label className="relative block">
        <span className="sr-only">Buscar por folio</span>
        <Search className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2" />
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Buscar por folio o mesa"
          autoFocus
          className="min-h-12 w-full border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] pl-11 pr-3 font-bold outline-none focus:bg-white"
        />
      </label>
      <div className="flex flex-wrap gap-2">
        <BrutalButton type="button" size="sm" variant="primary" disabled>Este corte</BrutalButton>
        {currentTableId !== null ? (
          <BrutalButton
            type="button"
            size="sm"
            variant={tableId === currentTableId ? "primary" : "secondary"}
            onClick={() => onTableChange(tableId === currentTableId ? undefined : currentTableId)}
          >
            Mesa actual
          </BrutalButton>
        ) : null}
        {[
          ["Cobrado", "Cobrados"],
          ["Cancelado", "Cancelados"],
        ].map(([value, label]) => (
          <BrutalButton
            key={value}
            type="button"
            size="sm"
            variant={status === value ? "primary" : "secondary"}
            onClick={() => onStatusChange(status === value ? undefined : value)}
          >
            {label}
          </BrutalButton>
        ))}
      </div>
    </div>
  );
}
