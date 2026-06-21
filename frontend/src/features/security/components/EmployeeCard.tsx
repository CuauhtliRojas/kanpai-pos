import type { Employee } from "../types/securityTypes";

type Props = {
  employee: Employee;
};

export function EmployeeCard({ employee }: Props) {
  return (
    <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard-sm)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate font-black uppercase">{employee.full_name}</p>
          {employee.pos_alias && employee.pos_alias !== employee.full_name && (
            <p className="text-xs font-bold text-[var(--kp-muted)]">{employee.pos_alias}</p>
          )}
          <p className="mt-0.5 text-xs font-bold text-[var(--kp-muted)]">
            {employee.employee_code}
          </p>
        </div>
        <span
          className={[
            "shrink-0 border-2 border-[var(--kp-ink)] px-2 py-0.5 text-xs font-black uppercase",
            employee.active
              ? "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]"
              : "bg-[var(--kp-surface-raised)] text-[var(--kp-muted)]",
          ].join(" ")}
        >
          {employee.active ? "Activo" : "Inactivo"}
        </span>
      </div>
    </div>
  );
}
