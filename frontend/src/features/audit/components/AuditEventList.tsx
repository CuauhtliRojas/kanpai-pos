import type { AuditEvent } from "../types/auditTypes";
import { AuditEventCard } from "./AuditEventCard";

export function AuditEventList({ events, onDetail }: { events: AuditEvent[]; onDetail: (event: AuditEvent) => void }) {
  if (events.length === 0) return <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center font-black uppercase shadow-[var(--kp-shadow-hard)]">Sin datos</div>;
  return <ul className="grid gap-3 md:grid-cols-2">{events.map((event) => <AuditEventCard key={event.id} event={event} onDetail={onDetail} />)}</ul>;
}
