import type { ReactNode } from "react";

type SurfaceCardProps = {
  title: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function SurfaceCard({ title, eyebrow, action, children }: SurfaceCardProps) {
  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <header className="mb-4 flex items-start justify-between gap-4 border-b-4 border-[var(--kp-ink)] pb-3">
        <div>
          {eyebrow ? (
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-warning)]">
              {eyebrow}
            </p>
          ) : null}
          <h2 className="mt-1 text-2xl font-black uppercase leading-none text-[var(--kp-text)]">
            {title}
          </h2>
        </div>
        {action}
      </header>
      {children}
    </section>
  );
}
