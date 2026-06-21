import { useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { ApiError } from "../../../api/http";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { TicketLine } from "../../tickets/types/ticketTypes";
import { useCancelTicketLineMutation } from "../hooks/useCancelTicketLineMutation";
import { useModifyTicketLineMutation } from "../hooks/useModifyTicketLineMutation";
import { CancelLineDialog } from "./CancelLineDialog";
import { ModifyLineDialog } from "./ModifyLineDialog";

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
  const [menuOpen, setMenuOpen] = useState(false);
  const [dialog, setDialog] = useState<"modify" | "cancel" | null>(null);
  const [note, setNote] = useState(line.note ?? "");
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const modifyMutation = useModifyTicketLineMutation();
  const cancelMutation = useCancelTicketLineMutation();
  const ticketAllowsAdjustments = ticketStatus === "Abierto" || ticketStatus === "En cobro";
  const lineIsActive = line.status !== "Cancelado";
  const canCancelThisLine = line.line_type !== "Componente de paquete";

  if (!ticketAllowsAdjustments || !lineIsActive) {
    return notice ? <p className="mt-2 text-xs font-black uppercase text-[var(--kp-success-text)]">{notice}</p> : null;
  }

  return (
    <div className="mt-2">
      <button
        type="button"
        aria-label="Acciones del producto"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((open) => !open)}
        className="flex min-h-10 w-12 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] shadow-[var(--kp-shadow-hard-sm)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
      >
        <MoreHorizontal className="h-6 w-6" />
      </button>

      {menuOpen ? (
        <div className="mt-3 grid gap-3 border-l-4 border-[var(--kp-selected)] pl-3">
          <BrutalButton
            type="button"
            size="sm"
            variant="secondary"
            onClick={() => {
              setNote(line.note ?? "");
              modifyMutation.reset();
              setDialog("modify");
            }}
          >
            Modificar
          </BrutalButton>
          {canCancelThisLine && canCancel ? (
            <BrutalButton
              type="button"
              size="sm"
              variant="danger"
              onClick={() => {
                setReason("");
                cancelMutation.reset();
                setDialog("cancel");
              }}
            >
              Cancelar producto
            </BrutalButton>
          ) : canCancelThisLine ? (
            <p className="text-xs font-black uppercase text-[var(--kp-warning-text)]">Pide autorización al encargado.</p>
          ) : null}
        </div>
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
              setMenuOpen(false);
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
              setMenuOpen(false);
            }).catch(() => undefined);
          }}
        />
      ) : null}
    </div>
  );
}
