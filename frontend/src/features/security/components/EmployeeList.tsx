import type { EmployeeDetail, EmployeeListItem } from "../types/securityTypes";
import { EmployeeCard } from "./EmployeeCard";

type Props = {
  employees: EmployeeListItem[];
  detailsByEmployeeId: Map<number, EmployeeDetail>;
  selectedEmployeeId: number | null;
  onViewDetail: (employeeId: number) => void;
};

export function EmployeeList({
  employees,
  detailsByEmployeeId,
  selectedEmployeeId,
  onViewDetail,
}: Props) {
  if (employees.length === 0) {
    return (
      <p className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-6 text-center font-black uppercase text-[var(--kp-muted)] shadow-[var(--kp-shadow-hard)]">
        Sin datos de empleados
      </p>
    );
  }
  return (
    <section className="grid gap-3">
      <div className="hidden border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] p-3 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-text-on-dark)] lg:grid lg:grid-cols-[minmax(180px,1.4fr)_120px_130px_minmax(160px,1fr)_130px]">
        <span>Empleado</span>
        <span>Código</span>
        <span>Estado</span>
        <span>Acceso y roles</span>
        <span className="text-right">Detalle</span>
      </div>
      <ul className="grid gap-3">
        {employees.map((employee) => (
          <li key={employee.id}>
            <EmployeeCard
              employee={employee}
              detail={detailsByEmployeeId.get(employee.id)}
              selected={selectedEmployeeId === employee.id}
              onViewDetail={onViewDetail}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
