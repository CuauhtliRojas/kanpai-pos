import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { ApiError } from "../../../api/http";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { useCancelTicketLineMutation } from "../hooks/useCancelTicketLineMutation";
import { useModifyTicketLineMutation } from "../hooks/useModifyTicketLineMutation";
import { CancelLineDialog } from "./CancelLineDialog";
import { ModifyLineDialog } from "./ModifyLineDialog";
import { TicketLineActionsDialog } from "./TicketLineActionsDialog";

type TicketLineActionsProps = {
  ticketId: number;
  ticketStatus: string;
  line: TicketLine;
  employeeId: number;
  canCancel: boolean;
};

function modificationError(error: unknown): string | null {
  if (!error) return null;
  return "No se pudo guardar la modificación.";
}

function cancellationError(error: unknown): string | null {
  if (!error) return null;
  if (error instanceof ApiError && error.status === 403) return "Pide autorización al encargado.";
  return "No se pudo cancelar.";
}

export function TicketLineActions({
  ticketId,
  ticketStatus,
  line,
  employeeId,
  canCancel,
}: TicketLineActionsProps) {
  const [actionsOpen, setActionsOpen] = useState(false);
  const [dialog, setDialog] = useState<"modify" | "cancel" | null>(null);
  const [note, setNote] = useState(line.note ?? "");
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const modifyMutation = useModifyTicketLineMutation();
  const cancelMutation = useCancelTicketLineMutation();
  const ticketAllowsAdjustments = ticketStatus === "Abierto" || ticketStatus === "En cobro";
  const lineIsActive = line.status !== "Cancelado";
  const canCancelThisLine = line.line_type !== "Componente de paquete";

  const canModify = ticketAllowsAdjustments && lineIsActive;
  const canCancelLine = canModify && canCancelThisLine && canCancel;

  return (
    <div>
      <button
        type="button"
        aria-label="Acciones del producto"
        aria-expanded={actionsOpen}
        onClick={() => setActionsOpen(true)}
        className="flex min-h-10 w-12 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
      >
        <MoreHorizontal className="h-6 w-6" />
      </button>

      {actionsOpen ? (
        <TicketLineActionsDialog
          line={line}
          canModify={canModify}
          canCancel={canCancelLine}
          requiresAuthorization={canModify && canCancelThisLine && !canCancel}
          onClose={() => setActionsOpen(false)}
          onModify={() => {
            setActionsOpen(false);
            setNote(line.note ?? "");
            modifyMutation.reset();
            setDialog("modify");
          }}
          onCancel={() => {
            setActionsOpen(false);
            setReason("");
            cancelMutation.reset();
            setDialog("cancel");
          }}
        />
      ) : null}

      {notice ? <p className="mt-2 text-xs font-black uppercase text-[var(--kp-success-text)]">{notice}</p> : null}

      {dialog === "modify" ? (
        <ModifyLineDialog
          productName={line.product_name_snapshot}
          note={note}
          isSaving={modifyMutation.isPending}
          errorMessage={modificationError(modifyMutation.error)}
          onNoteChange={setNote}
          onClose={() => setDialog(null)}
          onSubmit={() => {
            void modifyMutation.mutateAsync({
              ticketId,
              lineId: line.id,
              payload: { employee_id: employeeId, note: note.trim() },
            }).then(() => {
              setNotice(line.status === "Capturado" ? "Pendiente de enviar" : "Modificación enviada");
              setDialog(null);
            }).catch(() => undefined);
          }}
        />
      ) : null}

      {dialog === "cancel" ? (
        <CancelLineDialog
          productName={line.product_name_snapshot}
          reason={reason}
          isSaving={cancelMutation.isPending}
          errorMessage={cancellationError(cancelMutation.error)}
          onReasonChange={setReason}
          onClose={() => setDialog(null)}
          onSubmit={() => {
            void cancelMutation.mutateAsync({
              ticketId,
              lineId: line.id,
              payload: { employee_id: employeeId, reason: reason.trim() },
            }).then(() => {
              setNotice("Producto cancelado");
              setDialog(null);
            }).catch(() => undefined);
          }}
        />
      ) : null}
    </div>
  );
}
