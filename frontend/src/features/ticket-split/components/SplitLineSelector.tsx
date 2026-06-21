import type { TicketLine } from "../../tickets/types/ticketTypes";

type Props = { lines: TicketLine[]; usedIds: Set<number>; selectedIds: number[]; onChange: (ids: number[]) => void };
export function SplitLineSelector({ lines, usedIds, selectedIds, onChange }: Props) {
  const available = lines.filter((line) => line.status !== "Cancelado");
  return <div className="grid gap-2">{available.map((line) => {
    const used = usedIds.has(line.id);
    const checked = selectedIds.includes(line.id);
    return <label key={line.id} className="flex items-start gap-2 border-2 border-[var(--kp-ink)] p-2 font-bold"><input type="checkbox" disabled={used} checked={checked} onChange={() => onChange(checked ? selectedIds.filter((id) => id !== line.id) : [...selectedIds, line.id])} className="mt-1 h-5 w-5" /><span>{line.quantity} × {line.product_name_snapshot}{used ? " — Ya asignado" : ""}</span></label>;
  })}</div>;
}
