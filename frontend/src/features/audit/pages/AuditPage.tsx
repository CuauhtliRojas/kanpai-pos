import { RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { AuditDetailDialog } from "../components/AuditDetailDialog";
import { AuditEventList } from "../components/AuditEventList";
import { getAuditDetailTarget } from "../utils/auditFormatters";
import { useCashShiftAuditQuery, useTicketAuditQuery } from "../hooks/useAuditDetailQueries";
import { useAuditEventsQuery } from "../hooks/useAuditEventsQuery";
import type { AuditEvent, AuditEventFilters } from "../types/auditTypes";

type AuditRangePreset = "today" | "yesterday" | "last7" | "custom";
type AuditTypeFilter = "all" | "cash" | "ticket" | "product" | "production" | "printing" | "inventory" | "security";

const PAGE_LIMIT = 50;

const typeOptions: Array<{ value: AuditTypeFilter; label: string; entityType?: string }> = [
  { value: "all", label: "Todos" },
  { value: "cash", label: "Caja", entityType: "CashShift" },
  { value: "ticket", label: "Cuenta", entityType: "Ticket" },
  { value: "product", label: "Producto/venta", entityType: "TicketLine" },
  { value: "production", label: "Producción", entityType: "StationOrder" },
  { value: "printing", label: "Impresión", entityType: "PrintJob" },
  { value: "inventory", label: "Inventario", entityType: "InventoryMovement" },
  { value: "security", label: "Seguridad", entityType: "SmsNotification" },
];

function toLocalIsoDate(date: Date): string {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function getPresetRange(preset: Exclude<AuditRangePreset, "custom">): { dateFrom: string; dateTo: string } {
  const today = new Date();
  const from = new Date(today);
  const to = new Date(today);

  if (preset === "yesterday") {
    from.setDate(today.getDate() - 1);
    to.setDate(today.getDate() - 1);
  }

  if (preset === "last7") {
    from.setDate(today.getDate() - 6);
  }

  return { dateFrom: toLocalIsoDate(from), dateTo: toLocalIsoDate(to) };
}

function parsePositiveInt(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : undefined;
}

export function AuditPage() {
  const [rangePreset, setRangePreset] = useState<AuditRangePreset>("today");
  const [dateRange, setDateRange] = useState(() => getPresetRange("today"));
  const [typeFilter, setTypeFilter] = useState<AuditTypeFilter>("all");
  const [entityId, setEntityId] = useState("");
  const [eventType, setEventType] = useState("");
  const [actorEmployeeId, setActorEmployeeId] = useState("");
  const [offset, setOffset] = useState(0);
  const [selection, setSelection] = useState<{ ticketId: number | null; cashShiftId: number | null } | null>(null);

  const selectedType = typeOptions.find((option) => option.value === typeFilter);
  const filters: AuditEventFilters = {
    entityType: selectedType?.entityType,
    entityId: parsePositiveInt(entityId),
    eventType: eventType.trim() || undefined,
    actorEmployeeId: parsePositiveInt(actorEmployeeId),
    dateFrom: dateRange.dateFrom,
    dateTo: dateRange.dateTo,
    limit: PAGE_LIMIT,
    offset,
  };

  const eventsQuery = useAuditEventsQuery(filters);
  const ticketQuery = useTicketAuditQuery(selection?.ticketId ?? null);
  const cashShiftQuery = useCashShiftAuditQuery(selection?.ticketId === null ? selection.cashShiftId : null);
  const page = eventsQuery.data;
  const total = page?.total ?? 0;
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + PAGE_LIMIT, total);
  const canGoBack = offset > 0;
  const canGoNext = offset + PAGE_LIMIT < total;
  const eventTypeOptions = useMemo(
    () => Array.from(new Set((page?.items ?? []).map((event) => event.event_type))).sort((a, b) => a.localeCompare(b, "es")),
    [page?.items],
  );

  function resetToFirstPage() {
    setOffset(0);
  }

  function handleRangePreset(nextPreset: AuditRangePreset) {
    setRangePreset(nextPreset);
    resetToFirstPage();
    if (nextPreset !== "custom") {
      setDateRange(getPresetRange(nextPreset));
    }
  }

  function showDetail(event: AuditEvent) {
    const target = getAuditDetailTarget(event);
    if (target) setSelection(target);
  }

  return (
    <div className="grid gap-4">
      <header className="grid gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)] xl:grid-cols-[minmax(0,1fr)_auto] xl:items-start">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Eventos</p>
          <h1 className="mt-1 text-3xl font-black uppercase leading-none md:text-5xl">Auditoría</h1>
          <p className="mt-2 max-w-3xl text-sm font-bold text-[var(--kp-muted)] md:text-base">
            Revisa movimientos importantes del sistema.
          </p>
        </div>
        <BrutalButton onClick={() => void eventsQuery.refetch()} disabled={eventsQuery.isFetching}>
          <RefreshCw className="h-5 w-5" /> Actualizar
        </BrutalButton>
      </header>

      <section className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Periodo</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {[
              ["today", "Hoy"],
              ["yesterday", "Ayer"],
              ["last7", "Últimos 7 días"],
              ["custom", "Personalizado"],
            ].map(([value, label]) => (
              <BrutalButton
                key={value}
                type="button"
                size="sm"
                variant={rangePreset === value ? "warning" : "secondary"}
                onClick={() => handleRangePreset(value as AuditRangePreset)}
              >
                {label}
              </BrutalButton>
            ))}
          </div>
          {rangePreset === "custom" ? (
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
                Desde
                <input
                  type="date"
                  value={dateRange.dateFrom}
                  max={dateRange.dateTo}
                  onChange={(event) => {
                    if (!event.target.value) return;
                    setRangePreset("custom");
                    resetToFirstPage();
                    setDateRange((current) => ({ ...current, dateFrom: event.target.value }));
                  }}
                  className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
                />
              </label>
              <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
                Hasta
                <input
                  type="date"
                  value={dateRange.dateTo}
                  min={dateRange.dateFrom}
                  onChange={(event) => {
                    if (!event.target.value) return;
                    setRangePreset("custom");
                    resetToFirstPage();
                    setDateRange((current) => ({ ...current, dateTo: event.target.value }));
                  }}
                  className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
                />
              </label>
            </div>
          ) : null}
        </div>

        <div>
          <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">Tipo</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {typeOptions.map((option) => (
              <BrutalButton
                key={option.value}
                type="button"
                size="sm"
                variant={typeFilter === option.value ? "warning" : "secondary"}
                onClick={() => {
                  setTypeFilter(option.value);
                  resetToFirstPage();
                }}
              >
                {option.label}
              </BrutalButton>
            ))}
          </div>
        </div>

        <div className="grid gap-2 lg:grid-cols-3">
          <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            Buscar ID de entidad
            <input
              inputMode="numeric"
              value={entityId}
              onChange={(event) => {
                setEntityId(event.target.value);
                resetToFirstPage();
              }}
              placeholder="Ej. 125"
              className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
            />
          </label>
          <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            Event type
            <input
              list="audit-event-types"
              value={eventType}
              onChange={(event) => {
                setEventType(event.target.value);
                resetToFirstPage();
              }}
              placeholder="Opcional avanzado"
              className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
            />
            <datalist id="audit-event-types">
              {eventTypeOptions.map((option) => <option key={option} value={option} />)}
            </datalist>
          </label>
          <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            Empleado ID
            <input
              inputMode="numeric"
              value={actorEmployeeId}
              onChange={(event) => {
                setActorEmployeeId(event.target.value);
                resetToFirstPage();
              }}
              placeholder="Opcional"
              className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
            />
          </label>
        </div>
      </section>

      <section className="flex flex-wrap items-center justify-between gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
        <p className="font-black uppercase">
          Mostrando {start}-{end} de {total} eventos
        </p>
        <div className="flex gap-2">
          <BrutalButton type="button" size="sm" disabled={!canGoBack || eventsQuery.isFetching} onClick={() => setOffset(Math.max(0, offset - PAGE_LIMIT))}>
            Anterior
          </BrutalButton>
          <BrutalButton type="button" size="sm" disabled={!canGoNext || eventsQuery.isFetching} onClick={() => setOffset(offset + PAGE_LIMIT)}>
            Siguiente
          </BrutalButton>
        </div>
      </section>

      {eventsQuery.isPending ? <LoadingState /> : eventsQuery.isError ? (
        <ErrorState title="No se pudo cargar Auditoría" message="Intenta de nuevo." />
      ) : <AuditEventList events={eventsQuery.data?.items ?? []} onDetail={showDetail} />}

      {selection ? (
        <AuditDetailDialog
          ticket={ticketQuery.data ?? null}
          cashShift={cashShiftQuery.data ?? null}
          isLoading={selection.ticketId !== null ? ticketQuery.isPending : cashShiftQuery.isPending}
          hasError={selection.ticketId !== null ? ticketQuery.isError : cashShiftQuery.isError}
          onClose={() => setSelection(null)}
        />
      ) : null}
    </div>
  );
}
