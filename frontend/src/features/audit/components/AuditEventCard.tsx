import { formatNullableDate } from "../../../shared/lib/formatters";
import type { AuditEvent } from "../types/auditTypes";

export function AuditEventCard({ event }: { event: AuditEvent }) {
  return (
    <li className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard-sm)]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="font-black uppercase">{event.event_type}</p>
        <time className="text-sm font-bold text-[var(--kp-muted)]">{formatNullableDate(event.created_at)}</time>
      </div>
      {event.reason ? <p className="mt-2 border-l-4 border-[var(--kp-selected)] pl-2 font-bold">Motivo: {event.reason}</p> : null}
    </li>
  );
}
