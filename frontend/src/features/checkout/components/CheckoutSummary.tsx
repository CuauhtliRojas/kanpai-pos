import { formatCentsToPesos } from "../../../shared/lib/money";
import type { Ticket } from "../../tables/types/tableTypes";

type CheckoutSummaryProps = {
  ticket: Ticket;
  lineCount: number;
};

export function CheckoutSummary({ ticket, lineCount }: CheckoutSummaryProps) {
  return (
    <div className="mt-3 grid gap-2 bg-zinc-900 p-3 font-bold">
      <div className="flex justify-between gap-3">
        <span>Productos</span>
        <span>{lineCount}</span>
      </div>
      <div className="flex justify-between gap-3">
        <span>Subtotal</span>
        <span>{formatCentsToPesos(ticket.subtotal_cents)}</span>
      </div>
      <div className="flex justify-between gap-3 text-lg font-black">
        <span>Total</span>
        <span>{formatCentsToPesos(ticket.total_cents)}</span>
      </div>
    </div>
  );
}
