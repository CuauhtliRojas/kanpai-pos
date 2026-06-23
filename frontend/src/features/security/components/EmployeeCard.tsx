import { Eye } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import type { EmployeeDetail, EmployeeListItem } from "../types/securityTypes";

type Props = {
  employee: EmployeeListItem;
  detail?: EmployeeDetail;
  selected: boolean;
  onViewDetail: (employeeId: number) => void;
};

export function EmployeeCard({ employee, detail, selected, onViewDetail }: Props) {
  const roles = detail?.roles ?? [];

  return (
    <div
      className={[
        "grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)] lg:grid-cols-[minmax(180px,1.4fr)_120px_130px_minmax(160px,1fr)_130px]",
        selected ? "outline outline-4 outline-offset-2 outline-[var(--kp-selected)]" : "",
      ].join(" ")}
    >
      <div className="min-w-0">
        <p className="truncate font-black uppercase">{employee.full_name}</p>
        <p className="text-xs font-bold text-[var(--kp-muted)]">
          {employee.pos_alias && employee.pos_alias !== employee.full_name
            ? employee.pos_alias
            : "Sin alias POS"}
        </p>
      </div>

      <div>
        <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
          Código
        </p>
        <p className="font-bold uppercase">{employee.employee_code}</p>
      </div>

      <div className="flex items-start">
        <span
          className={[
            "border-2 border-[var(--kp-ink)] px-2 py-1 text-xs font-black uppercase",
            employee.active
              ? "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]"
              : "bg-[var(--kp-surface-raised)] text-[var(--kp-muted)]",
          ].join(" ")}
        >
          {employee.active ? "Activo" : "Inactivo"}
        </span>
      </div>

      <div className="min-w-0">
        <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
          Acceso
        </p>
        <p className="font-bold uppercase">
          {detail ? (detail.pin_enabled ? "PIN activo" : "Sin PIN") : "Abrir detalle"}
        </p>
        <p className="truncate text-xs font-bold text-[var(--kp-muted)]">
          {roles.length > 0
            ? roles.map((role) => role.role_key).join(", ")
            : detail
            ? "Sin roles"
            : "Abrir detalle"}
        </p>
      </div>

      <div className="flex items-center justify-start lg:justify-end">
        <BrutalButton type="button" size="sm" onClick={() => onViewDetail(employee.id)}>
          <Eye className="h-4 w-4" />
          Ver detalle
        </BrutalButton>
      </div>
    </div>
  );
}
