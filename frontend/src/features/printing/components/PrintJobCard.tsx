import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatNullableDate } from "../../../shared/lib/formatters";
import type { PrintJob } from "../types/printingTypes";
import { PrintStatusBadge } from "./PrintStatusBadge";

type Props = {
  job: PrintJob;
  canReprint: boolean;
  isReprinting: boolean;
  errorMessage: string | null;
  onReprint: (reason: string) => Promise<void>;
};

export function PrintJobCard({ job, canReprint, isReprinting, errorMessage, onReprint }: Props) {
  const [showReason, setShowReason] = useState(false);
  const [reason, setReason] = useState("");

  return (
    <article className="grid gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <header className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-2xl font-black uppercase">{job.folio}</h2>
          <p className="mt-1 font-bold text-[var(--kp-muted)]">{job.job_type}</p>
        </div>
        <PrintStatusBadge status={job.status} />
      </header>
      <p className="text-sm font-bold">Solicitado: {formatNullableDate(job.created_at)}</p>
      {errorMessage ? (
        <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3 font-bold text-[var(--kp-danger-text)]">{errorMessage}</p>
      ) : null}
      {canReprint && showReason ? (
        <form
          className="grid gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            const cleanReason = reason.trim();
            if (!cleanReason) return;
            void onReprint(cleanReason)
              .then(() => { setReason(""); setShowReason(false); })
              .catch(() => undefined);
          }}
        >
          <label className="grid gap-2 text-sm font-black uppercase tracking-[0.08em]">
            Motivo
            <input
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              maxLength={200}
              className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] px-3 text-base font-bold normal-case tracking-normal text-[var(--kp-text)] outline-none focus:border-[var(--kp-info)]"
            />
          </label>
          <BrutalButton type="submit" disabled={isReprinting || !reason.trim()} fullWidth>Reimprimir</BrutalButton>
        </form>
      ) : canReprint ? (
        <BrutalButton onClick={() => setShowReason(true)} fullWidth>Reimprimir</BrutalButton>
      ) : null}
    </article>
  );
}
