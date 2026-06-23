import { ChevronDown } from "lucide-react";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { formatPermissionLabel } from "../lib/permissionDisplay";
import type { Permission, Role } from "../types/securityTypes";

type Props = {
  roles: Role[];
  permissions: Permission[];
  isLoading: boolean;
  hasError: boolean;
  accessDenied: boolean;
};

export function SystemRolesPanel({
  roles,
  permissions,
  isLoading,
  hasError,
  accessDenied,
}: Props) {
  const activePermissions = permissions.filter((permission) => permission.active).length;

  return (
    <details className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] shadow-[var(--kp-shadow-hard-sm)]">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 p-4">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
            Consulta
          </p>
          <h2 className="text-xl font-black uppercase">Roles del sistema</h2>
          <p className="mt-1 text-sm font-bold text-[var(--kp-muted)]">
            {permissions.length > 0
              ? `${activePermissions} permisos activos de ${permissions.length} registrados`
              : "Roles y permisos configurados para el personal"}
          </p>
        </div>
        <ChevronDown className="h-6 w-6 shrink-0" />
      </summary>

      <div className="border-t-4 border-[var(--kp-ink)] p-4">
        {isLoading ? <LoadingState /> : null}
        {hasError ? (
          <ErrorState
            title="No se pudieron cargar los roles"
            message={
              accessDenied
                ? "No tienes permiso para ver esta información."
                : "Intenta de nuevo."
            }
          />
        ) : null}
        {!isLoading && !hasError ? (
          roles.length > 0 ? (
            <div className="grid gap-3">
              {roles.map((role) => (
                <article
                  key={role.id}
                  className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] p-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <h3 className="font-black uppercase">{role.name}</h3>
                      <p className="text-xs font-bold uppercase text-[var(--kp-muted)]">
                        {role.role_key}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <span
                        className={[
                          "border-2 border-[var(--kp-ink)] px-2 py-1 text-xs font-black uppercase",
                          role.active
                            ? "bg-[var(--kp-success)] text-[var(--kp-success-contrast)]"
                            : "bg-[var(--kp-surface)] text-[var(--kp-muted)]",
                        ].join(" ")}
                      >
                        {role.active ? "Activo" : "Inactivo"}
                      </span>
                      <span className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-2 py-1 text-xs font-black uppercase">
                        {role.permissions.length} permisos
                      </span>
                    </div>
                  </div>
                  {role.permissions.length > 0 ? (
                    <ul className="mt-3 flex flex-wrap gap-2">
                      {role.permissions.map((permission) => (
                        <li
                          key={permission.id}
                          className="border-2 border-[var(--kp-ink)] bg-[var(--kp-surface)] px-2 py-1 text-xs font-bold"
                        >
                          {formatPermissionLabel(permission.permission_key)}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-3 text-sm font-bold text-[var(--kp-muted)]">
                      Sin permisos incluidos.
                    </p>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <p className="text-sm font-bold text-[var(--kp-muted)]">Sin roles registrados.</p>
          )
        ) : null}
      </div>
    </details>
  );
}
