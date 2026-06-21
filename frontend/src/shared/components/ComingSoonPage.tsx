type ComingSoonPageProps = {
  title: string;
};

export function ComingSoonPage({ title }: ComingSoonPageProps) {
  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-5 text-[var(--kp-text)] shadow-[var(--kp-shadow-hard)]">
      <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
        {title}
      </p>
      <h1 className="mt-2 text-3xl font-black uppercase leading-tight">Módulo en preparación</h1>
    </section>
  );
}
