import type { ProductionOrderLine } from "../types/productionTypes";

export function ProductionOrderLines({ lines }: { lines: ProductionOrderLine[] }) {
  return (
    <ul className="grid gap-2">
      {lines.map((line) => (
        <li key={line.id} className="border-t-2 border-zinc-700 pt-2 first:border-t-0 first:pt-0">
          <div className="flex items-start justify-between gap-4 font-black">
            <span>{line.product_name_snapshot}</span>
            <span className="shrink-0 text-lg">{line.quantity}</span>
          </div>
          {line.note_snapshot ? (
            <p className="mt-1 text-sm font-bold text-[var(--kp-warning-text)]">
              {line.note_snapshot}
            </p>
          ) : null}
          {line.line_action !== "Agregar" ? (
            <p className="mt-1 text-xs font-black uppercase text-[var(--kp-muted)]">
              {line.line_action}
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
