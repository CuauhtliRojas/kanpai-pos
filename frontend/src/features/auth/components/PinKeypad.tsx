import { Delete } from "lucide-react";

type PinKeypadProps = {
  onDigit: (digit: string) => void;
  onBackspace: () => void;
  onClear: () => void;
  disabled?: boolean;
};

const digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9"];
const keyClassName =
  "flex h-12 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] text-lg font-black text-[var(--kp-text)] shadow-[var(--kp-shadow-hard-sm)] transition active:translate-x-[3px] active:translate-y-[3px] active:shadow-none disabled:cursor-not-allowed disabled:opacity-45";

export function PinKeypad({ onDigit, onBackspace, onClear, disabled = false }: PinKeypadProps) {
  return (
    <div className="grid grid-cols-3 gap-1.5" aria-label="Teclado numerico">
      {digits.map((digit) => (
        <button key={digit} type="button" disabled={disabled} className={keyClassName} onClick={() => onDigit(digit)}>
          {digit}
        </button>
      ))}
      <button type="button" disabled={disabled} className={keyClassName} onClick={onClear}>Borrar</button>
      <button type="button" disabled={disabled} className={keyClassName} onClick={() => onDigit("0")}>0</button>
      <button type="button" disabled={disabled} aria-label="Borrar ultimo numero" className={keyClassName} onClick={onBackspace}>
        <Delete className="h-5 w-5" />
      </button>
    </div>
  );
}
