import type { ReactNode } from "react";

export function ReportCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
      <h2 className="text-xl font-black uppercase">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}
