import { formatCentsToPesos } from "../../../shared/lib/money";
import type { Ticket } from "../../tables/types/tableTypes";

type CheckoutSummaryProps = {
  ticket: Ticket;
  lineCount: number;
  remainingCents?: number;
  embedded?: boolean;
};

export function CheckoutSummary({ ticket, lineCount, remainingCents, embedded = false }: CheckoutSummaryProps) {
  const balanceCents = remainingCents ?? ticket.total_cents;

  return (
    <div className={`grid gap-1 bg-[var(--kp-bg-alt)] p-2 font-bold ${embedded ? "" : "mt-2 border-2 border-[var(--kp-divider)]"}`}>
      <div className="flex justify-between gap-2">
        <span>Productos</span>
        <span>{lineCount}</span>
      </div>
      <div className="flex justify-between gap-2">
        <span>Subtotal</span>
        <span>{formatCentsToPesos(ticket.subtotal_cents)}</span>
      </div>
      {embedded ? (
        <div className="flex justify-between gap-2">
          <span>Descuento</span>
          <span>-{formatCentsToPesos(ticket.discount_cents)}</span>
        </div>
      ) : null}
      <div className={`flex justify-between gap-2 border-t-2 border-[var(--kp-divider)] pt-1 font-black ${embedded ? "" : "text-lg"}`}>
        <span>Total</span>
        <span>{formatCentsToPesos(ticket.total_cents)}</span>
      </div>
      {embedded ? (
        <div className="flex justify-between gap-2 text-lg font-black">
          <span>Saldo</span>
          <span>{formatCentsToPesos(balanceCents)}</span>
        </div>
      ) : null}
    </div>
  );
}
