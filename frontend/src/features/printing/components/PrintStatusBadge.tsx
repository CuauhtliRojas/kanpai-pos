import { StatusBadge } from "../../../shared/components/StatusBadge";
import type { PrintJobStatus } from "../types/printingTypes";

const statusTone = {
  Pendiente: "warning",
  Tomado: "info",
  Impreso: "ok",
  Fallido: "danger",
  Cancelado: "neutral",
} as const;

const statusLabel: Record<PrintJobStatus, string> = {
  Pendiente: "Pendiente",
  Tomado: "En proceso",
  Impreso: "Impreso",
  Fallido: "Falló",
  Cancelado: "Cancelado",
};

export function PrintStatusBadge({ status }: { status: PrintJobStatus }) {
  return <StatusBadge label={statusLabel[status]} tone={statusTone[status]} />;
}
