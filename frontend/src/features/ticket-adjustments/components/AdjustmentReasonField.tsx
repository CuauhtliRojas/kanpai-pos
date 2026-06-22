type AdjustmentReasonFieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  optional?: boolean;
  compact?: boolean;
};

export function AdjustmentReasonField({
  label,
  value,
  onChange,
  disabled = false,
  optional = false,
  compact = false,
}: AdjustmentReasonFieldProps) {
  return (
    <label className="grid gap-2 text-sm font-black uppercase tracking-[0.08em]">
      {label}
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
        rows={compact ? 2 : 3}
        required={!optional}
        className={`resize-none border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] text-base font-bold normal-case tracking-normal text-[var(--kp-text)] outline-none focus:border-[var(--kp-info)] disabled:opacity-50 ${compact ? "p-2" : "p-3"}`}
      />
    </label>
  );
}
