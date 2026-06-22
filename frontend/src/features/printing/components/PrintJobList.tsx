import type { PrintJob } from "../types/printingTypes";
import { PrintJobCard } from "./PrintJobCard";

type Props = {
  jobs: PrintJob[];
  canReprint: boolean;
  activeJobId: number | null;
  isReprinting: boolean;
  reprintError: string | null;
  onReprint: (jobId: number, reason: string) => Promise<void>;
};

export function PrintJobList({ jobs, canReprint, activeJobId, isReprinting, reprintError, onReprint }: Props) {
  if (jobs.length === 0) {
    return (
      <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-10 text-center shadow-[var(--kp-shadow-hard)]">
        <p className="text-xl font-black uppercase">Sin impresiones pendientes</p>
        <p className="mt-2 font-bold text-[var(--kp-muted)]">
          Cuando haya tickets o comandas por imprimir apareceran aqui.
        </p>
      </div>
    );
  }
  return (
    <div className="grid items-start gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {jobs.map((job) => (
        <PrintJobCard
          key={job.id}
          job={job}
          canReprint={canReprint}
          isReprinting={activeJobId === job.id && isReprinting}
          reprintError={activeJobId === job.id ? reprintError : null}
          onReprint={(reason) => onReprint(job.id, reason)}
        />
      ))}
    </div>
  );
}
