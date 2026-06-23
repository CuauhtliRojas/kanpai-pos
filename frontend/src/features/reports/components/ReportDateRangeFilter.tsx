import { CalendarDays } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { ReportDateRange } from "../types/reportTypes";

export type ReportRangePreset = "today" | "yesterday" | "last7" | "custom";

type Props = {
  preset: ReportRangePreset;
  range: ReportDateRange;
  onPresetChange: (preset: ReportRangePreset) => void;
  onRangeChange: (range: ReportDateRange) => void;
};

const presets: Array<{ value: ReportRangePreset; label: string }> = [
  { value: "today", label: "Hoy" },
  { value: "yesterday", label: "Ayer" },
  { value: "last7", label: "Últimos 7 días" },
  { value: "custom", label: "Personalizado" },
];

export function toLocalIsoDate(date: Date): string {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

export function getPresetRange(preset: Exclude<ReportRangePreset, "custom">): ReportDateRange {
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

export function ReportDateRangeFilter({ preset, range, onPresetChange, onRangeChange }: Props) {
  return (
    <section className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
      <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-selected)]">
        <CalendarDays className="h-4 w-4" aria-hidden="true" />
        Periodo
      </div>
      <div className="flex flex-wrap gap-2">
        {presets.map((item) => (
          <BrutalButton
            key={item.value}
            type="button"
            size="sm"
            variant={preset === item.value ? "warning" : "secondary"}
            onClick={() => onPresetChange(item.value)}
          >
            {item.label}
          </BrutalButton>
        ))}
      </div>
      {preset === "custom" ? (
        <div className="grid gap-2 sm:grid-cols-2">
          <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            Desde
            <input
              type="date"
              value={range.dateFrom}
              max={range.dateTo}
              onChange={(event) => {
                if (event.target.value) onRangeChange({ ...range, dateFrom: event.target.value });
              }}
              className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
            />
          </label>
          <label className="grid gap-1 text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">
            Hasta
            <input
              type="date"
              value={range.dateTo}
              min={range.dateFrom}
              onChange={(event) => {
                if (event.target.value) onRangeChange({ ...range, dateTo: event.target.value });
              }}
              className="min-h-11 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 font-black text-[var(--kp-text)] outline-none focus:bg-white focus:text-[var(--kp-ink)]"
            />
          </label>
        </div>
      ) : null}
    </section>
  );
}
