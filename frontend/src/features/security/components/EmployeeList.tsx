import type { Employee } from "../types/securityTypes";
import { EmployeeCard } from "./EmployeeCard";

type Props = {
  employees: Employee[];
};

export function EmployeeList({ employees }: Props) {
  if (employees.length === 0) {
    return (
      <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-6 text-center font-black uppercase text-[var(--kp-muted)] shadow-[var(--kp-shadow-hard)]">
        Sin datos de empleados
      </p>
    );
  }
  const active = employees.filter((e) => e.active);
  const inactive = employees.filter((e) => !e.active);
  return (
    <div className="grid gap-4">
      {active.length > 0 && (
        <section>
          <p className="mb-2 text-xs font-black uppercase tracking-[0.15em] text-[var(--kp-muted)]">
            Activos ({active.length})
          </p>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {active.map((emp) => (
              <li key={emp.id}>
                <EmployeeCard employee={emp} />
              </li>
            ))}
          </ul>
        </section>
      )}
      {inactive.length > 0 && (
        <section>
          <p className="mb-2 text-xs font-black uppercase tracking-[0.15em] text-[var(--kp-muted)]">
            Inactivos ({inactive.length})
          </p>
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {inactive.map((emp) => (
              <li key={emp.id}>
                <EmployeeCard employee={emp} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
