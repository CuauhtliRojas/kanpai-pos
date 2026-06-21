type TableStatusBadgeProps = {
  status: string;
  selected: boolean;
};

export function TableStatusBadge({ status, selected }: TableStatusBadgeProps) {
  const isFree = status === "Libre";
  const label = selected
    ? "Mesa seleccionada"
    : isFree
      ? "Mesa libre"
      : "Mesa ocupada";
  const className = selected
    ? "bg-[var(--kp-selected)] text-[var(--kp-selected-contrast)]"
    : isFree
      ? "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]"
      : "bg-[var(--kp-info)] text-[var(--kp-info-contrast)]";

  return (
    <span
      className={`inline-flex border-4 border-[var(--kp-ink)] px-2 py-1 text-[10px] font-black uppercase tracking-[0.08em] ${className}`}
    >
      {label}
    </span>
  );
}
