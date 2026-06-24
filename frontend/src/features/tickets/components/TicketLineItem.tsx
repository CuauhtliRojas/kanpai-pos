import type { ReactNode } from "react";
import { formatCentsToPesos } from "../../../shared/lib/money";
import type { TicketLine } from "../types/ticketTypes";

function optionLabel(name: string): string {
  return name
    .replace(/^brochetas?\s+de\s+/i, "")
    .replace(/^brochetas?\s+/i, "")
    .trim();
}

function variantSummaries(line: TicketLine): string[] {
  const groups = new Map<string, TicketLine["variant_selections"]>();
  for (const selection of line.variant_selections) {
    const current = groups.get(selection.group_name) ?? [];
    current.push(selection);
    groups.set(selection.group_name, current);
  }

  return [...groups.entries()].map(([groupName, selections]) => {
    const isPreparation = groupName.toLocaleLowerCase().includes("prepar");
    const values = selections.map((selection) => {
      const name = optionLabel(selection.name_snapshot);
      return isPreparation ? name : `${name} x${selection.quantity}`;
    });
    const label = groupName.toLocaleUpperCase().includes("BROCHETA")
      ? "Brochetas"
      : groupName;
    return `${label}: ${values.join(", ")}`;
  });
}

export function TicketLineItem({ line, actions }: { line: TicketLine; actions?: ReactNode }) {
  const variants = variantSummaries(line);

  if (line.line_type === "Componente de paquete") {
    return (
      <li className="border-b border-dashed border-[var(--kp-divider)] py-1.5 pl-4 last:border-b-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-bold text-[var(--kp-muted)]">
            · {line.product_name_snapshot}
          </p>
          <span className="text-xs font-bold text-[var(--kp-muted)]">incluido</span>
        </div>
      </li>
    );
  }

  return (
    <li className="border-b-2 border-[var(--kp-divider)] py-3 last:border-b-0">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
        <div>
          <p className="font-black leading-tight">{line.product_name_snapshot}</p>
          {variants.length > 0 ? (
            <div className="mt-1 grid gap-0.5 text-sm font-bold text-[var(--kp-text-muted)]">
              {variants.map((summary) => <p key={summary}>{summary}</p>)}
            </div>
          ) : null}
          <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
            {line.quantity} × {formatCentsToPesos(line.unit_price_cents)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <p className="shrink-0 font-black">{formatCentsToPesos(line.line_total_cents)}</p>
          {actions}
        </div>
      </div>
      {line.status === "Capturado" ? (
        <p className="mt-1 inline-flex border-2 border-[var(--kp-ink)] bg-[var(--kp-warning)] px-2 py-1 text-xs font-black uppercase tracking-wide text-[var(--kp-warning-contrast)]">
          Pendiente de enviar
        </p>
      ) : null}
      {line.status === "Cancelado" ? (
        <p className="mt-1 text-xs font-black uppercase tracking-wide text-[var(--kp-danger-text)]">
          Cancelado
        </p>
      ) : null}
      {line.status !== "Capturado" && line.status !== "Cancelado" ? (
        <p className="mt-1 inline-flex border-2 border-[var(--kp-ink)] bg-[var(--kp-info-bg)] px-2 py-1 text-xs font-black uppercase tracking-wide">
          Enviado
        </p>
      ) : null}
      {line.note ? (
        <p className="mt-2 border-l-4 border-[var(--kp-selected)] pl-2 text-sm font-bold">
          Nota: {line.note}
        </p>
      ) : null}
    </li>
  );
}
