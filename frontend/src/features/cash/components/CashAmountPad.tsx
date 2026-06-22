import { BrutalButton } from "../../../shared/components/BrutalButton";

const amountKeys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "00", "."];

export function normalizeCashAmount(value: string): string | null {
  if (!/^\d*(?:\.\d{0,2})?$/.test(value)) return null;

  const [integerPart, decimalPart] = value.split(".");
  const normalizedInteger = integerPart.replace(/^0+(?=\d)/, "");
  return decimalPart === undefined ? normalizedInteger : `${normalizedInteger || "0"}.${decimalPart}`;
}

function appendAmountValue(currentValue: string, value: string): string {
  if (value === ".") {
    if (currentValue.includes(".")) return currentValue;
    return currentValue ? `${currentValue}.` : "0.";
  }

  const decimalPart = currentValue.split(".")[1];
  if (decimalPart !== undefined) {
    return decimalPart.length >= 2
      ? currentValue
      : `${currentValue}${value.slice(0, 2 - decimalPart.length)}`;
  }

  if (!currentValue || currentValue === "0") {
    return value.replace(/^0+/, "") || "0";
  }

  return `${currentValue}${value}`;
}

type CashAmountPadProps = {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  label?: string;
};

export function CashAmountPad({
  value,
  onChange,
  disabled = false,
  label = "Teclado numérico",
}: CashAmountPadProps) {
  return (
    <div className="grid content-start gap-2" aria-label={label}>
      <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-muted)]">Teclado</p>
      <div className="grid grid-cols-3 gap-2">
        {amountKeys.map((key) => (
          <BrutalButton
            key={key}
            type="button"
            size="md"
            disabled={disabled}
            onClick={() => onChange(appendAmountValue(value, key))}
          >
            {key}
          </BrutalButton>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-2">
        <BrutalButton
          type="button"
          size="md"
          disabled={disabled}
          onClick={() => onChange(value.slice(0, -1))}
        >
          Borrar
        </BrutalButton>
        <BrutalButton type="button" variant="warning" size="md" disabled={disabled} onClick={() => onChange("")}>
          Limpiar
        </BrutalButton>
      </div>
    </div>
  );
}
