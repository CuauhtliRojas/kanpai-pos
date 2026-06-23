import { X } from "lucide-react";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { formatPermissionLabel, groupPermissions } from "../lib/permissionDisplay";
import type {
  EmployeeDetail,
  EmployeeListItem,
  EmployeePermissions,
} from "../types/securityTypes";

type Props = {
  employee: EmployeeListItem;
  detail: EmployeeDetail | undefined;
  employeePermissions: EmployeePermissions | undefined;
  isLoading: boolean;
  hasError: boolean;
  accessDenied: boolean;
  onClose: () => void;
};

function formatDate(value: string | null | undefined) {
  if (!value) return "Sin registro";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Sin registro";

  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span
      className={[
        "inline-flex border-2 border-[var(--kp-ink)] px-2 py-1 text-xs font-black uppercase",
        active
          ? "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]"
          : "bg-[var(--kp-surface-raised)] text-[var(--kp-muted)]",
      ].join(" ")}
    >
      {active ? "Activo" : "Inactivo"}
    </span>
  );
}

export function EmployeeDetailDialog({
  employee,
  detail,
  employeePermissions,
  isLoading,
  hasError,
  accessDenied,
  onClose,
}: Props) {
  const roles = employeePermissions?.roles ?? detail?.roles ?? [];
  const permissions = employeePermissions?.permissions ?? [];
  const groupedPermissions = groupPermissions(permissions);

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-[rgba(0,0,0,0.78)] p-3"
      role="dialog"
      aria-modal="true"
      aria-labelledby="employee-detail-title"
      onClick={onClose}
    >
      <aside
        className="flex max-h-full w-full max-w-3xl flex-col overflow-y-auto border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-3 border-b-4 border-[var(--kp-ink)] pb-3">
          <div className="min-w-0">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
              Detalle de empleado
            </p>
            <h2 id="employee-detail-title" className="mt-1 truncate text-2xl font-black uppercase">
              {detail?.full_name ?? employee.full_name}
            </h2>
            <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
              {detail?.pos_alias || employee.pos_alias || "Sin alias POS"} - Código{" "}
              {detail?.employee_code ?? employee.employee_code}
            </p>
          </div>
          <button
            type="button"
            aria-label="Cerrar"
            className="flex h-11 w-11 shrink-0 items-center justify-center border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)]"
            onClick={onClose}
          >
            <X className="h-6 w-6" />
          </button>
        </header>

        {isLoading ? <div className="mt-4"><LoadingState /></div> : null}

        {hasError ? (
          <div className="mt-4">
            <ErrorState
              title="No se pudo cargar el detalle"
              message={
                accessDenied
                  ? "No tienes permiso para ver esta información."
                  : "Intenta de nuevo."
              }
            />
          </div>
        ) : null}

        {!isLoading && !hasError && detail ? (
          <div className="mt-4 grid gap-4">
            <section className="grid gap-3 border-4 border-[var(--kp-ink)] bg-[var(--kp-bg)] p-3 text-[var(--kp-text-on-dark)]">
              <div className="grid gap-3 sm:grid-cols-3">
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-muted)]">
                    Estado
                  </p>
                  <div className="mt-1">
                    <StatusBadge active={detail.active} />
                  </div>
                </div>
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-muted)]">
                    PIN
                  </p>
                  <p className="mt-1 font-black uppercase">
                    {detail.pin_enabled ? "PIN activo" : "Sin PIN"}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-black uppercase tracking-[0.14em] text-[var(--kp-muted)]">
                    Último acceso
                  </p>
                  <p className="mt-1 font-bold">{formatDate(detail.last_login_at)}</p>
                </div>
              </div>
            </section>

            <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
              <h3 className="text-sm font-black uppercase tracking-[0.12em]">
                Roles asignados
              </h3>
              {roles.length > 0 ? (
                <ul className="mt-3 flex flex-wrap gap-2">
                  {roles.map((role) => (
                    <li
                      key={role.id}
                      className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-2 py-1 text-xs font-black uppercase"
                    >
                      {role.name} / {role.role_key}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
                  Sin roles asignados.
                </p>
              )}
            </section>

            <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3">
              <h3 className="text-sm font-black uppercase tracking-[0.12em]">
                Permisos efectivos
              </h3>
              {permissions.length > 0 ? (
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  {groupedPermissions.map((group) => (
                    <div key={group.title} className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3">
                      <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-selected)]">
                        {group.title}
                      </p>
                      {group.permissions.length > 0 ? (
                        <ul className="mt-2 grid gap-1">
                          {group.permissions.map((permission) => (
                            <li key={permission.id} className="text-sm font-bold">
                              {formatPermissionLabel(permission.permission_key)}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="mt-2 text-sm font-bold text-[var(--kp-muted)]">
                          Sin permisos.
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
                  Sin permisos efectivos.
                </p>
              )}
            </section>
          </div>
        ) : null}

        <div className="mt-4">
          <BrutalButton type="button" onClick={onClose} fullWidth>
            Cerrar
          </BrutalButton>
        </div>
      </aside>
    </div>
  );
}
