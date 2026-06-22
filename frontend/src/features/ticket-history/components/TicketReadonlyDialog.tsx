import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatNullableDate } from "../../../shared/lib/formatters";
import { formatCentsToPesos } from "../../../shared/lib/money";
import { useReadonlyTicketQuery } from "../hooks/useReadonlyTicketQuery";
import { ReprintTicketAction } from "./ReprintTicketAction";

type Props = {
  ticketId: number;
  employeeId: number | null;
  canReprint: boolean;
  onClose: () => void;
  onQueued: () => void;
};

export function TicketReadonlyDialog({ ticketId, employeeId, canReprint, onClose, onQueued }: Props) {
  const query = useReadonlyTicketQuery(ticketId);
  const detail = query.data;
  const ticketPrintJob = detail?.print_jobs.find((job) => job.job_type === "Ticket") ?? null;
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-3" role="dialog" aria-modal="true">
      <section className="max-h-[94vh] w-full max-w-3xl overflow-y-auto border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <header className="flex items-start justify-between gap-3">
          <div><p className="text-xs font-black uppercase text-[var(--kp-selected)]">Solo lectura</p><h2 className="text-2xl font-black uppercase">Detalle de ticket</h2></div>
          <button type="button" aria-label="Cerrar detalle" onClick={onClose} className="flex h-11 w-11 items-center justify-center border-4 border-[var(--kp-ink)]"><X /></button>
        </header>
        {query.isPending ? <p className="mt-4 font-black uppercase">Consultando...</p> : query.isError || !detail ? (
          <p className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold">No se pudo cargar el ticket.</p>
        ) : (
          <div className="mt-4 grid gap-4">
            <div className="grid gap-2 border-4 border-[var(--kp-ink)] p-3 sm:grid-cols-[1fr_auto]">
              <div><p className="text-2xl font-black">{detail.ticket.folio}</p><p className="font-bold">{detail.table.display_name} · {detail.ticket.status}</p><p className="text-sm font-bold text-[var(--kp-muted)]">{formatNullableDate(detail.ticket.paid_at ?? detail.ticket.opened_at)}</p></div>
              <p className="text-2xl font-black sm:text-right">{formatCentsToPesos(detail.ticket.total_cents)}</p>
            </div>
            <section><h3 className="mb-2 text-lg font-black uppercase">Productos</h3><div className="grid gap-2">{detail.lines.map((line) => <div key={line.id} className="border-2 border-[var(--kp-ink)] p-3"><div className="flex justify-between gap-3"><p className="font-black">{line.quantity} × {line.product_name_snapshot}</p><p className="font-black">{formatCentsToPesos(line.line_total_cents)}</p></div>{line.variant_selections.length ? <p className="text-sm font-bold text-[var(--kp-muted)]">{line.variant_selections.map((item) => item.name_snapshot).join(" · ")}</p> : null}{line.note ? <p className="text-sm font-bold">Nota: {line.note}</p> : null}</div>)}</div></section>
            {detail.discounts.length ? <section><h3 className="mb-2 text-lg font-black uppercase">Descuentos</h3>{detail.discounts.map((item) => <p key={item.id} className="border-2 border-[var(--kp-ink)] p-3 font-bold">{item.discount_type}: -{formatCentsToPesos(item.amount_cents)}{item.reason ? ` · ${item.reason}` : ""}</p>)}</section> : null}
            <section><h3 className="mb-2 text-lg font-black uppercase">Pagos</h3>{detail.payments.length ? detail.payments.map((payment) => <div key={payment.id} className="mb-2 flex justify-between gap-3 border-2 border-[var(--kp-ink)] p-3"><div><p className="font-black">{payment.payment_method_name}</p><p className="text-sm font-bold text-[var(--kp-muted)]">{payment.folio}{payment.reference ? ` · ${payment.reference}` : ""}</p></div><p className="font-black">{formatCentsToPesos(payment.amount_cents)}</p></div>) : <p className="font-bold text-[var(--kp-muted)]">Sin pagos registrados.</p>}</section>
            <section><h3 className="mb-2 text-lg font-black uppercase">Impresiones</h3><p className="font-bold">{detail.print_jobs.length} trabajo(s) de impresión · {detail.station_orders.length} comanda(s)</p></section>
            {canReprint && employeeId !== null && ticketPrintJob ? <ReprintTicketAction ticketId={ticketId} printJobId={ticketPrintJob.id} employeeId={employeeId} onQueued={onQueued} /> : null}
            <BrutalButton type="button" onClick={onClose}>Cerrar</BrutalButton>
          </div>
        )}
      </section>
    </div>
  );
}
