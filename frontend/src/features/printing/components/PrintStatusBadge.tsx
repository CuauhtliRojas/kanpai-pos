import { StatusBadge } from "../../../shared/components/StatusBadge";
import type { PrintJobStatus } from "../types/printingTypes";

const statusTone = {
  Pendiente: "warning",
  Tomado: "info",
  Impreso: "ok",
  Fallido: "danger",
  Cancelado: "neutral",
} as const;

export function PrintStatusBadge({ status }: { status: PrintJobStatus }) {
  const label = status === "Pendiente" ? "Impresión pendiente" : status === "Fallido" ? "Falló" : status;
  return <StatusBadge label={label} tone={statusTone[status]} />;
}
