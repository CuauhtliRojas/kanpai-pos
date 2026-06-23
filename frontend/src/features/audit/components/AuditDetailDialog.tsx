import { X } from "lucide-react";
import { formatNullableDate } from "../../../shared/lib/formatters";
import { formatCentsToPesos } from "../../../shared/lib/money";
import { formatAuditEventTitle, getAuditCategory, getAuditSeverity } from "../utils/auditFormatters";
import type { AuditEvent, CashShiftAudit, TicketAudit } from "../types/auditTypes";

type Props = {
  ticket: TicketAudit | null;
  cashShift: CashShiftAudit | null;
  isLoading: boolean;
  hasError: boolean;
  onClose: () => void;
};

const eventToneClassName = {
  neutral: "border-zinc-700",
  warning: "border-[var(--kp-warning)]",
  danger: "border-[var(--kp-danger)]",
  success: "border-[var(--kp-success)]",
};

function DetailStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border-2 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-2">
      <p className="break-words text-lg font-black">{value}</p>
      <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">{label}</p>
    </div>
  );
}

function DetailEventTimeline({ events }: { events: AuditEvent[] }) {
  if (events.length === 0) {
    return <p className="font-bold text-[var(--kp-muted)]">Sin eventos registrados.</p>;
  }

  return (
    <ol className="grid gap-2">
      {events.map((event) => (
        <li key={event.id} className={`border-l-4 bg-zinc-900 px-3 py-2 ${eventToneClassName[getAuditSeverity(event)]}`}>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-black">{formatAuditEventTitle(event.event_type)}</p>
            <time className="text-xs font-bold text-[var(--kp-muted)]">{formatNullableDate(event.created_at)}</time>
          </div>
          <p className="mt-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-selected)]">{getAuditCategory(event)}</p>
          {event.reason ? <p className="mt-1 text-sm font-bold">Motivo: {event.reason}</p> : null}
        </li>
      ))}
    </ol>
  );
}

function TicketDetail({ detail }: { detail: TicketAudit }) {
  return (
    <div className="mt-4 grid gap-4">
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Ticket</p>
            <h3 className="text-2xl font-black uppercase">{detail.ticket.folio}</h3>
          </div>
          <p className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1 text-sm font-black uppercase">
            {detail.ticket.status} · {detail.ticket.payment_status}
          </p>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <DetailStat label="Total" value={formatCentsToPesos(detail.ticket.total_cents)} />
          <DetailStat label="Descuento" value={formatCentsToPesos(detail.ticket.discount_cents)} />
          <DetailStat label="Apertura" value={formatNullableDate(detail.ticket.opened_at)} />
          <DetailStat label="Pago" value={formatNullableDate(detail.ticket.paid_at)} />
        </div>
        {detail.ticket.cancel_reason ? <p className="mt-3 border-l-4 border-[var(--kp-danger)] pl-2 font-bold">Motivo: {detail.ticket.cancel_reason}</p> : null}
      </section>

      <section>
        <h4 className="text-sm font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Conteos</h4>
        <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <DetailStat label="Productos" value={detail.lines.length} />
          <DetailStat label="Pagos" value={detail.payments.length} />
          <DetailStat label="Descuentos" value={detail.discounts.length} />
          <DetailStat label="Comandas" value={detail.station_orders.length} />
          <DetailStat label="Impresiones" value={detail.print_jobs.length} />
          <DetailStat label="Movimientos" value={detail.inventory_movements.length} />
          <DetailStat label="Cambios" value={detail.modifications.length} />
          <DetailStat label="Eventos" value={detail.audit_events.length} />
        </div>
      </section>

      <section>
        <h4 className="text-sm font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Timeline</h4>
        <div className="mt-2 max-h-80 overflow-y-auto pr-1">
          <DetailEventTimeline events={detail.audit_events} />
        </div>
      </section>
    </div>
  );
}

function CashShiftDetail({ detail }: { detail: CashShiftAudit }) {
  return (
    <div className="mt-4 grid gap-4">
      <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Corte</p>
            <h3 className="text-2xl font-black uppercase">{detail.cash_shift.folio}</h3>
          </div>
          <p className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-2 py-1 text-sm font-black uppercase">{detail.cash_shift.status}</p>
        </div>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <DetailStat label="Apertura" value={formatNullableDate(detail.cash_shift.opened_at)} />
          <DetailStat label="Cierre" value={formatNullableDate(detail.cash_shift.closed_at)} />
          <DetailStat label="Fondo inicial" value={formatCentsToPesos(detail.cash_shift.opening_cash_cents)} />
          <DetailStat label="Diferencia" value={formatCentsToPesos(detail.cash_shift.cash_difference_cents)} />
        </div>
        {detail.cash_shift.closing_note ? <p className="mt-3 border-l-4 border-[var(--kp-selected)] pl-2 font-bold">Nota: {detail.cash_shift.closing_note}</p> : null}
      </section>

      <section>
        <h4 className="text-sm font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Resumen</h4>
        <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <DetailStat label="Ventas" value={formatCentsToPesos(detail.summary.total_sales_cents)} />
          <DetailStat label="Pagado" value={formatCentsToPesos(detail.summary.total_paid_cents)} />
          <DetailStat label="Gastos" value={formatCentsToPesos(detail.summary.total_expenses_cents)} />
          <DetailStat label="Cuentas" value={detail.summary.ticket_count} />
          <DetailStat label="Cobradas" value={detail.summary.paid_ticket_count} />
          <DetailStat label="Canceladas" value={detail.summary.cancelled_ticket_count} />
          <DetailStat label="Impresiones pendientes" value={detail.summary.pending_print_jobs_count} />
          <DetailStat label="Eventos" value={detail.audit_events.length} />
        </div>
      </section>

      <section>
        <h4 className="text-sm font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Eventos</h4>
        <div className="mt-2 max-h-80 overflow-y-auto pr-1">
          <DetailEventTimeline events={detail.audit_events} />
        </div>
      </section>
    </div>
  );
}

export function AuditDetailDialog({ ticket, cashShift, isLoading, hasError, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(0,0,0,0.78)] p-4" role="dialog" aria-modal="true" aria-labelledby="audit-detail-title">
      <section className="max-h-[90vh] w-full max-w-4xl overflow-y-auto border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <header className="flex justify-between gap-3">
          <div>
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">Auditoría</p>
            <h2 id="audit-detail-title" className="text-2xl font-black uppercase">Detalle</h2>
          </div>
          <button type="button" aria-label="Cerrar" onClick={onClose} className="flex h-11 w-11 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)]">
            <X className="h-6 w-6" />
          </button>
        </header>

        {isLoading ? (
          <p className="mt-4 font-black uppercase">Consultando...</p>
        ) : hasError ? (
          <p className="mt-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">No se pudo cargar el detalle.</p>
        ) : ticket ? (
          <TicketDetail detail={ticket} />
        ) : cashShift ? (
          <CashShiftDetail detail={cashShift} />
        ) : (
          <p className="mt-4 font-bold text-[var(--kp-muted)]">No hay detalle disponible.</p>
        )}
      </section>
    </div>
  );
}
