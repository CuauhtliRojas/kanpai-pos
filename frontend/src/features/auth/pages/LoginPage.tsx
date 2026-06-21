import { BrandMark } from "../../../shared/components/BrandMark";
import { LoginPanel } from "../components/LoginPanel";

export function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--kp-bg)] p-3 text-[var(--kp-text)]">
      <section className="w-full max-w-[480px] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div className="mb-3 flex justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-2">
          <BrandMark variant="logo" className="h-10 w-auto max-w-full" />
        </div>
        <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">Acceso de personal</p>
        <h1 className="mb-3 mt-1 text-3xl font-black uppercase leading-none">Iniciar sesión</h1>
        <LoginPanel />
      </section>
    </main>
  );
}
