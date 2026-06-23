import type { ReactNode } from "react";

type Props = {
  label: string;
  value: number;
  maxValue: number;
  valueLabel: ReactNode;
  meta?: ReactNode;
  rank?: number;
  tone?: "success" | "warning" | "danger" | "neutral";
};

const barClassName: Record<NonNullable<Props["tone"]>, string> = {
  success: "bg-[var(--kp-success)]",
  warning: "bg-[var(--kp-warning)]",
  danger: "bg-[var(--kp-danger)]",
  neutral: "bg-[var(--kp-selected)]",
};

export function ReportBarRow({ label, value, maxValue, valueLabel, meta, rank, tone = "neutral" }: Props) {
  const width = maxValue > 0 ? Math.max(4, Math.round((value / maxValue) * 100)) : 0;

  return (
    <div className="grid gap-2 border-t-2 border-zinc-700 py-2 first:border-t-0 first:pt-0">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
        <div className="min-w-0">
          <p className="truncate font-black">
            {rank ? <span className="mr-2 text-[var(--kp-selected)]">#{rank}</span> : null}
            {label}
          </p>
          {meta ? <div className="mt-1 text-xs font-bold uppercase tracking-[0.04em] text-[var(--kp-muted)]">{meta}</div> : null}
        </div>
        <p className="shrink-0 text-right font-black">{valueLabel}</p>
      </div>
      <div className="h-3 border-2 border-[var(--kp-ink)] bg-[var(--kp-bg)]">
        <div className={`h-full ${barClassName[tone]}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}
