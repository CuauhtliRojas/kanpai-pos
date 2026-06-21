import { useAuthSession } from "../hooks/useAuthSession";

export function SessionSummary() {
  const { employee } = useAuthSession();
  const cashierName = employee?.pos_alias?.trim() || employee?.full_name || "";

  return (
    <div className="flex min-w-0 items-center">
      <span className="min-w-0 truncate text-xs font-black uppercase tracking-[0.06em] sm:text-sm">
        <span className="hidden text-[var(--kp-muted)] lg:inline">Cajero: </span>{cashierName}
      </span>
    </div>
  );
}
