type AdjustmentReasonFieldProps = {
  label: "Nota" | "Motivo";
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export function AdjustmentReasonField({
  label,
  value,
  onChange,
  disabled = false,
}: AdjustmentReasonFieldProps) {
  return (
    <label className="grid gap-2 text-sm font-black uppercase tracking-[0.08em]">
      {label}
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        rows={3}
        required
        className="resize-none border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] p-3 text-base font-bold normal-case tracking-normal text-[var(--kp-text)] outline-none focus:border-[var(--kp-info)] disabled:opacity-50"
      />
    </label>
  );
}
