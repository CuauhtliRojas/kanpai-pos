import type { PrintJob } from "../types/printingTypes";
import { PrintJobCard } from "./PrintJobCard";

type Props = {
  jobs: PrintJob[];
  canReprint: boolean;
  activeJobId: number | null;
  isReprinting: boolean;
  errorMessage: string | null;
  onReprint: (jobId: number, reason: string) => Promise<void>;
};

export function PrintJobList({ jobs, canReprint, activeJobId, isReprinting, errorMessage, onReprint }: Props) {
  if (jobs.length === 0) {
    return <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-8 text-center text-xl font-black uppercase shadow-[var(--kp-shadow-hard)]">Sin impresiones pendientes</div>;
  }
  return (
    <div className="grid items-start gap-4 md:grid-cols-2 xl:grid-cols-3">
      {jobs.map((job) => (
        <PrintJobCard
          key={job.id}
          job={job}
          canReprint={canReprint}
          isReprinting={activeJobId === job.id && isReprinting}
          errorMessage={activeJobId === job.id ? errorMessage : null}
          onReprint={(reason) => onReprint(job.id, reason)}
        />
      ))}
    </div>
  );
}
