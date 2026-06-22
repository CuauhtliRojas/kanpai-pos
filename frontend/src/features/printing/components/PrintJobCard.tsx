import { useState } from "react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { formatNullableDate } from "../../../shared/lib/formatters";
import type { PrintJob } from "../types/printingTypes";
import { PrintStatusBadge } from "./PrintStatusBadge";
import { ReprintJobDialog } from "./ReprintJobDialog";

function normalizeJobType(jobType: string): string {
  const map: Record<string, string> = {
    ticket: "Ticket",
    comanda: "Comanda",
    corte: "Corte",
  };
  return map[jobType.toLowerCase()] ?? jobType;
}

function formatPrinterKey(key: string): string {
  return key
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

type Props = {
  job: PrintJob;
  canReprint: boolean;
  isReprinting: boolean;
  reprintError: string | null;
  onReprint: (reason: string) => Promise<void>;
};

export function PrintJobCard({ job, canReprint, isReprinting, reprintError, onReprint }: Props) {
  const [dialogOpen, setDialogOpen] = useState(false);

  async function handleReprint(reason: string) {
    await onReprint(reason);
    setDialogOpen(false);
  }

  return (
    <>
      <article className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <header className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-black uppercase leading-tight">{job.folio}</h2>
            <p className="mt-0.5 text-sm font-bold text-[var(--kp-muted)]">{normalizeJobType(job.job_type)}</p>
          </div>
          <PrintStatusBadge status={job.status} />
        </header>

        <dl className="grid gap-1.5 text-sm">
          <div className="flex justify-between gap-2">
            <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Destino</dt>
            <dd className="text-right font-bold">{formatPrinterKey(job.printer_key_snapshot)}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Solicitado</dt>
            <dd className="text-right font-bold">{formatNullableDate(job.created_at)}</dd>
          </div>
          <div className="flex justify-between gap-2">
            <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Intentos</dt>
            <dd className="text-right font-bold">{job.attempts}</dd>
          </div>
          {job.claimed_at ? (
            <div className="flex justify-between gap-2">
              <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Tomado</dt>
              <dd className="text-right font-bold">{formatNullableDate(job.claimed_at)}</dd>
            </div>
          ) : null}
          {job.printed_at ? (
            <div className="flex justify-between gap-2">
              <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Impreso</dt>
              <dd className="text-right font-bold">{formatNullableDate(job.printed_at)}</dd>
            </div>
          ) : null}
          {job.failed_at ? (
            <div className="flex justify-between gap-2">
              <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Fallo</dt>
              <dd className="text-right font-bold">{formatNullableDate(job.failed_at)}</dd>
            </div>
          ) : null}
          {job.next_retry_at ? (
            <div className="flex justify-between gap-2">
              <dt className="font-black uppercase tracking-[0.08em] text-[var(--kp-muted)]">Siguiente intento</dt>
              <dd className="text-right font-bold">{formatNullableDate(job.next_retry_at)}</dd>
            </div>
          ) : null}
        </dl>

        {job.last_error ? (
          <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-3">
            <p className="text-xs font-black uppercase tracking-[0.08em] text-[var(--kp-danger-text)]">
              Problema reportado
            </p>
            <p
              className="mt-1 line-clamp-3 text-sm font-bold text-[var(--kp-danger-text)]"
              title={job.last_error}
            >
              {job.last_error}
            </p>
          </div>
        ) : null}

        {canReprint ? (
          <BrutalButton type="button" onClick={() => setDialogOpen(true)} fullWidth>
            Imprimir otra vez
          </BrutalButton>
        ) : null}
      </article>

      {dialogOpen ? (
        <ReprintJobDialog
          job={job}
          isSubmitting={isReprinting}
          errorMessage={reprintError}
          onSubmit={handleReprint}
          onClose={() => {
            if (!isReprinting) setDialogOpen(false);
          }}
        />
      ) : null}
    </>
  );
}
