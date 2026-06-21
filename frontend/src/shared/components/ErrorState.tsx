type ErrorStateProps = {
  title?: string;
  message: string;
};

export function ErrorState({
  title = "No se pudo cargar la información",
  message,
}: ErrorStateProps) {
  return (
    <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-danger-bg)] p-4 text-[var(--kp-danger-text)] shadow-[var(--kp-shadow-hard-sm)]" role="alert">
      <p className="text-lg font-black uppercase tracking-[0.08em]">{title}</p>
      <p className="mt-2 text-sm font-bold">{message}</p>
    </div>
  );
}
