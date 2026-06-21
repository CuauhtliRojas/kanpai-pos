type StatusBadgeTone = "ok" | "warning" | "danger" | "neutral" | "info";

type StatusBadgeProps = {
  label: string;
  tone?: StatusBadgeTone;
};

const toneClassName: Record<StatusBadgeTone, string> = {
  ok: "border-[var(--kp-ink)] bg-[var(--kp-success)] text-[var(--kp-success-contrast)]",
  warning: "border-[var(--kp-ink)] bg-[var(--kp-warning)] text-[var(--kp-warning-contrast)]",
  danger: "border-[var(--kp-ink)] bg-[var(--kp-danger)] text-[var(--kp-danger-contrast)]",
  neutral: "border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-[var(--kp-text)]",
  info: "border-[var(--kp-ink)] bg-[var(--kp-info)] text-[var(--kp-info-contrast)]",
};

export function StatusBadge({ label, tone = "neutral" }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex min-h-10 items-center whitespace-nowrap border-4 px-3 text-xs font-black uppercase tracking-[0.08em] shadow-[var(--kp-shadow-hard-sm)] ${toneClassName[tone]}`}
    >
      {label}
    </span>
  );
}
