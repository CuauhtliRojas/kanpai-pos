import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { Ticket } from "../../tables/types/tableTypes";
import { useCancelTicketMutation } from "../hooks/useCancelTicketMutation";
import { CancelTicketDialog } from "./CancelTicketDialog";

type Props = { ticket: Ticket; employeeId: number | null; canCancel: boolean; onCancelled: () => void };

export function CancelTicketAction({ ticket, employeeId, canCancel, onCancelled }: Props) {
  const [open, setOpen] = useState(false);
  const mutation = useCancelTicketMutation();
  const allowedStatus = ticket.status !== "Cobrado" && ticket.status !== "Cancelado";
  if (!canCancel || !allowedStatus) return null;
  return (
    <div>
      <BrutalButton type="button" variant="danger" size="sm" fullWidth onClick={() => setOpen(true)}>Cancelar cuenta completa</BrutalButton>
      {open && employeeId !== null ? (
        <CancelTicketDialog
          folio={ticket.folio}
          isSaving={mutation.isPending}
          errorMessage={mutation.isError ? "No se pudo cancelar la cuenta. Revisa su estado e intenta de nuevo." : null}
          onClose={() => { mutation.reset(); setOpen(false); }}
          onSubmit={(reason) => void mutation.mutateAsync({ ticketId: ticket.id, payload: { employee_id: employeeId, reason } }).then((result) => { if (result.table_released) onCancelled(); setOpen(false); }).catch(() => undefined)}
        />
      ) : null}
    </div>
  );
}
