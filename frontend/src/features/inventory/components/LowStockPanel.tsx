import { AlertTriangle } from "lucide-react";
import type { StockAlert } from "../types/inventoryTypes";

type Props = {
  alerts: StockAlert[];
};

export function LowStockPanel({ alerts }: Props) {
  if (alerts.length === 0) return null;
  return (
    <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-4 text-[var(--kp-warning-contrast)] shadow-[var(--kp-shadow-hard)]">
      <p className="flex items-center gap-2 text-sm font-black uppercase tracking-[0.1em]">
        <AlertTriangle className="h-5 w-5 shrink-0" />
        Bajo stock ({alerts.length})
      </p>
      <ul className="mt-2 grid gap-1">
        {alerts.map((alert) => (
          <li
            key={alert.id}
            className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-2 text-sm font-bold text-[var(--kp-text)]"
          >
            {alert.message}
          </li>
        ))}
      </ul>
    </div>
  );
}
