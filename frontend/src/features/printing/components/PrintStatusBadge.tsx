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
  return <StatusBadge label={status === "Fallido" ? "Falló" : status} tone={statusTone[status]} />;
}
