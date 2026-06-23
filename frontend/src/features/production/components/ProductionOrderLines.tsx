import type { ProductionOrderLine } from "../types/productionTypes";

function getLineActionLabel(value: string): string | null {
  const normalized = value.trim().toLowerCase();
  if (!normalized || normalized === "agregar" || normalized === "normal") return null;
  if (normalized === "modificar" || normalized === "modificacion" || normalized === "modificación") {
    return "Modificación";
  }
  if (normalized === "cancelar" || normalized === "cancelacion" || normalized === "cancelación") {
    return "Cancelación";
  }
  return value;
}

type ProductionOrderLinesProps = {
  lines: ProductionOrderLine[];
  compact?: boolean;
};

export function ProductionOrderLines({ lines, compact = false }: ProductionOrderLinesProps) {
  return (
    <ul className={compact ? "grid gap-1" : "grid gap-2"} aria-label="Productos">
      {lines.map((line) => {
        const note = line.note_snapshot?.trim();
        const lineActionLabel = getLineActionLabel(line.line_action);

        return (
          <li
            key={line.id}
            className={`grid gap-2 border-t-2 border-[var(--kp-divider)] first:border-t-0 first:pt-0 ${
              compact ? "grid-cols-[2.5rem_1fr] pt-2" : "grid-cols-[3.25rem_1fr] gap-3 pt-3"
            }`}
          >
            <span
              className={`flex items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] font-black shadow-[var(--kp-shadow-hard-sm)] ${
                compact ? "min-h-9 text-lg" : "min-h-12 text-2xl"
              }`}
            >
              {line.quantity}
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-start gap-2">
                <p className={`min-w-0 flex-1 font-black leading-tight ${compact ? "text-sm" : "text-base"}`}>
                  {line.product_name_snapshot}
                </p>
                {lineActionLabel ? (
                  <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-warning-bg)] px-2 py-1 text-[10px] font-black uppercase tracking-[0.08em] text-[var(--kp-warning-text)]">
                    {lineActionLabel}
                  </span>
                ) : null}
              </div>
              {note ? (
                <p
                  className={`mt-2 border-2 border-[var(--kp-ink)] bg-[var(--kp-warning-bg)] px-2 py-1 font-bold text-[var(--kp-warning-text)] ${
                    compact ? "text-xs" : "text-sm"
                  }`}
                >
                  Nota: {note}
                </p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
