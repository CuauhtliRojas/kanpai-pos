import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { useReprintJobMutation } from "../hooks/useReprintJobMutation";

type Props = { ticketId: number; printJobId: number; employeeId: number; onQueued: () => void };

export function ReprintTicketAction({ ticketId, printJobId, employeeId, onQueued }: Props) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const mutation = useReprintJobMutation(ticketId);
  if (!open) {
    return <BrutalButton type="button" onClick={() => setOpen(true)}>Reimprimir ticket</BrutalButton>;
  }
  return (
    <form
      className="grid gap-2 border-4 border-[var(--kp-ink)] bg-[var(--kp-bg-alt)] p-3"
      onSubmit={(event) => {
        event.preventDefault();
        const cleanReason = reason.trim();
        if (!cleanReason) return;
        void mutation.mutateAsync({ jobId: printJobId, employeeId, reason: cleanReason })
          .then(() => { setOpen(false); setReason(""); onQueued(); })
          .catch(() => undefined);
      }}
    >
      <label className="font-black uppercase" htmlFor="reprint-reason">Motivo de reimpresión</label>
      <textarea
        id="reprint-reason"
        value={reason}
        onChange={(event) => setReason(event.target.value)}
        rows={2}
        className="border-4 border-[var(--kp-ink)] bg-white p-2 font-bold"
      />
      {mutation.isError ? <p className="font-bold text-[var(--kp-danger-text)]">No se pudo enviar la reimpresión.</p> : null}
      <div className="flex flex-wrap gap-2">
        <BrutalButton type="submit" disabled={!reason.trim() || mutation.isPending}>Enviar a cola</BrutalButton>
        <BrutalButton type="button" onClick={() => setOpen(false)} disabled={mutation.isPending}>Volver</BrutalButton>
      </div>
    </form>
  );
}
