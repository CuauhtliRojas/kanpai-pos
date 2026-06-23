import type { ReactNode } from "react";

type KpiTone = "success" | "warning" | "danger" | "neutral";

type Props = {
  label: string;
  value: ReactNode;
  detail?: string;
  tone?: KpiTone;
};

const toneClassName: Record<KpiTone, string> = {
  success: "bg-[var(--kp-success-bg)] text-[var(--kp-success-text)]",
  warning: "bg-[var(--kp-warning-bg)] text-[var(--kp-warning-text)]",
  danger: "bg-[var(--kp-danger-bg)] text-[var(--kp-danger-text)]",
  neutral: "bg-[var(--kp-surface)] text-[var(--kp-text)]",
};

export function KpiTile({ label, value, detail, tone = "neutral" }: Props) {
  return (
    <article className={`min-w-0 border-4 border-[var(--kp-ink)] p-3 shadow-[var(--kp-shadow-hard-sm)] ${toneClassName[tone]}`}>
      <p className="truncate text-xs font-black uppercase tracking-[0.12em] opacity-80">{label}</p>
      <p className="mt-1 break-words text-2xl font-black leading-none md:text-3xl">{value}</p>
      {detail ? <p className="mt-2 text-xs font-bold uppercase tracking-[0.06em] opacity-80">{detail}</p> : null}
    </article>
  );
}
