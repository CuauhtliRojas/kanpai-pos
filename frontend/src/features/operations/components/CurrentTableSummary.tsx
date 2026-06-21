import { useCurrentOperation } from "../hooks/useCurrentOperation";

export function CurrentTableSummary() {
  const { selectedTable } = useCurrentOperation();
  const tableLabel =
    selectedTable?.display_name.trim() ||
    selectedTable?.table_code.trim() ||
    (selectedTable ? `Mesa ${selectedTable.id}` : "Sin mesa");

  return (
    <span className="hidden truncate text-xs font-black uppercase tracking-[0.08em] md:block">
      Mesa: {tableLabel}
    </span>
  );
}
