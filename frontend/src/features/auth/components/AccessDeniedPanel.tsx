export function AccessDeniedPanel() {
  return (
    <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-warning)] p-5 text-[var(--kp-ink)] shadow-[var(--kp-shadow-hard)]">
      <h1 className="text-2xl font-black uppercase leading-tight">
        No tienes permiso para usar esta opción.
      </h1>
      <p className="mt-3 text-base font-bold">Pide ayuda al encargado.</p>
    </section>
  );
}
