import { formatNullableDate } from "../../../shared/lib/formatters";
import { formatAuditEventTitle, formatEntityLabel, getAuditCategory, getAuditDetailTarget, getAuditSeverity } from "../utils/auditFormatters";
import type { AuditEvent } from "../types/auditTypes";

const badgeClassName = {
  neutral: "bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
  warning: "bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  danger: "bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
  success: "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
};

function formatDay(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-MX", { dateStyle: "medium" }).format(date);
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("es-MX", { timeStyle: "short" }).format(date);
}

function metadataValue(metadata: Record<string, unknown> | null | undefined, key: string): string | null {
  const containers = [metadata?.after, metadata?.before, metadata];
  for (const container of containers) {
    if (!container || typeof container !== "object") continue;
    const value = (container as Record<string, unknown>)[key];
    if (typeof value === "string" && value.trim()) return value;
    if (typeof value === "number") return String(value);
  }
  return null;
}

export function AuditEventList({ events, onDetail }: { events: AuditEvent[]; onDetail: (event: AuditEvent) => void }) {
  if (events.length === 0) {
    return (
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center font-black uppercase shadow-[var(--kp-shadow-hard)]">
        Sin eventos para los filtros seleccionados
      </div>
    );
  }

  let lastDay = "";

  return (
    <ol className="grid gap-2">
      {events.map((event) => {
        const day = formatDay(event.created_at);
        const showDay = day !== lastDay;
        const category = getAuditCategory(event);
        const severity = getAuditSeverity(event);
        const detailTarget = getAuditDetailTarget(event);
        const folio = metadataValue(event.metadata, "folio");
        lastDay = day;

        return (
          <li key={event.id} className="grid gap-2">
            {showDay ? <div className="mt-2 border-y-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] px-3 py-2 text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">{day}</div> : null}
            <article className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)] lg:grid-cols-[8rem_minmax(0,1fr)_auto] lg:items-start">
              <time className="font-black text-[var(--kp-selected)]" dateTime={event.created_at}>
                {formatTime(event.created_at)}
                <span className="block text-xs font-bold text-[var(--kp-muted)]">{formatNullableDate(event.created_at)}</span>
              </time>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`border-2 border-[var(--kp-ink)] px-2 py-1 text-xs font-black uppercase ${badgeClassName[severity]}`}>{category}</span>
                  <h2 className="text-base font-black uppercase">{formatAuditEventTitle(event.event_type)}</h2>
                </div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm font-bold text-[var(--kp-muted)]">
                  <span>Entidad: {formatEntityLabel(event)}</span>
                  {folio ? <span>Folio: {folio}</span> : null}
                  {event.actor_employee_id !== null ? <span>Empleado ID: {event.actor_employee_id}</span> : null}
                </div>
                {event.reason ? <p className="mt-2 border-l-4 border-[var(--kp-selected)] pl-2 text-sm font-bold">Motivo: {event.reason}</p> : null}
              </div>
              {detailTarget ? (
                <button
                  type="button"
                  onClick={() => onDetail(event)}
                  className="min-h-[var(--kp-touch-sm)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-sm font-black uppercase shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                >
                  Ver detalle
                </button>
              ) : null}
            </article>
          </li>
        );
      })}
    </ol>
  );
}
