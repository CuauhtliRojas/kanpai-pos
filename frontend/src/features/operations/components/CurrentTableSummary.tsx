import { useCurrentOperation } from "../hooks/useCurrentOperation";

export function CurrentTableSummary() {
  const { selectedTable } = useCurrentOperation();
  const tableLabel =
    selectedTable?.display_name.trim() ||
    selectedTable?.table_code.trim() ||
    (selectedTable ? "Mesa seleccionada" : "Sin mesa");

  return (
    <span className="hidden min-w-0 truncate border-l-2 border-[var(--kp-divider)] pl-2 text-xs font-black uppercase tracking-[0.06em] md:block">
      <span className="text-[var(--kp-muted)]">Mesa actual: </span>{tableLabel}
    </span>
  );
}
