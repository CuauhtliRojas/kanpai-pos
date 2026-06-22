import { formatCentsToPesos } from "../../../shared/lib/money";
import type { Ticket } from "../../tables/types/tableTypes";

type CheckoutSummaryProps = {
  ticket: Ticket;
  lineCount: number;
};

export function CheckoutSummary({ ticket, lineCount }: CheckoutSummaryProps) {
  return (
    <div className="mt-2 grid gap-1 border-2 border-[var(--kp-divider)] bg-[var(--kp-bg-alt)] p-2 font-bold">
      <div className="flex justify-between gap-2">
        <span>Productos</span>
        <span>{lineCount}</span>
      </div>
      <div className="flex justify-between gap-2">
        <span>Subtotal</span>
        <span>{formatCentsToPesos(ticket.subtotal_cents)}</span>
      </div>
      <div className="flex justify-between gap-2 border-t-2 border-[var(--kp-divider)] pt-1 text-lg font-black">
        <span>Total</span>
        <span>{formatCentsToPesos(ticket.total_cents)}</span>
      </div>
    </div>
  );
}
