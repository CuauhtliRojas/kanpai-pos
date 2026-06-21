type ComingSoonPageProps = {
  title: string;
};

export function ComingSoonPage({ title }: ComingSoonPageProps) {
  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
        {title}
      </p>
      <h1 className="mt-2 text-3xl font-black uppercase leading-tight">
        No disponible en esta versión
      </h1>
      <p className="mt-3 max-w-2xl font-bold text-[var(--kp-muted)]">
        Esta opción todavía no forma parte de la operación disponible.
      </p>
    </section>
  );
}
