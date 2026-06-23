import { useMemo, useState } from "react";
import { useQueries } from "@tanstack/react-query";
import { RefreshCw, Search } from "lucide-react";
import { ApiError } from "../../../api/http";
import { queryKeys } from "../../../api/queryKeys";
import { BrutalButton } from "../../../shared/components/BrutalButton";
import { ErrorState } from "../../../shared/components/ErrorState";
import { LoadingState } from "../../../shared/components/LoadingState";
import { useAuthSession } from "../../auth/hooks/useAuthSession";
import { getEmployeeDetail } from "../api/securityApi";
import { EmployeeDetailDialog } from "../components/EmployeeDetailDialog";
import { EmployeeList } from "../components/EmployeeList";
import { SystemRolesPanel } from "../components/SystemRolesPanel";
import {
  useEmployeeDetailQuery,
  useEmployeePermissionsQuery,
  useEmployeesQuery,
  usePermissionsQuery,
  useRolesQuery,
} from "../hooks/useEmployeesQuery";

const defaultRoleFilters = ["ADMIN", "GERENTE", "CAJERO", "ALMACEN", "SOPORTE"];

type StatusFilter = "all" | "active" | "inactive";
type PinFilter = "all" | "enabled" | "disabled";

function isAccessDenied(error: unknown) {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

function normalize(value: string | null | undefined) {
  return (value ?? "").trim().toLowerCase();
}

function KpiTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-3 shadow-[var(--kp-shadow-hard-sm)]">
      <p className="text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
        {label}
      </p>
      <p className="mt-1 text-3xl font-black uppercase">{value}</p>
    </div>
  );
}

export function SecurityPage() {
  const { sessionToken } = useAuthSession();
  const employeesQuery = useEmployeesQuery();
  const rolesQuery = useRolesQuery(sessionToken);
  const permissionsQuery = usePermissionsQuery(sessionToken);
  const employees = employeesQuery.data ?? [];

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [roleFilter, setRoleFilter] = useState("all");
  const [pinFilter, setPinFilter] = useState<PinFilter>("all");
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);

  const employeeDetailsQueries = useQueries({
    queries: employees.map((employee) => ({
      queryKey: queryKeys.security.employeeDetail(employee.id),
      queryFn: () => {
        if (!sessionToken) throw new Error("No hay sesión activa.");
        return getEmployeeDetail(employee.id, sessionToken);
      },
      enabled: Boolean(sessionToken),
      retry: false,
    })),
  });

  const selectedDetailQuery = useEmployeeDetailQuery(
    selectedEmployeeId,
    sessionToken,
    selectedEmployeeId !== null,
  );
  const selectedPermissionsQuery = useEmployeePermissionsQuery(
    selectedEmployeeId,
    sessionToken,
    selectedEmployeeId !== null,
  );

  const detailsByEmployeeId = useMemo(() => {
    const details = new Map<number, NonNullable<(typeof employeeDetailsQueries)[number]["data"]>>();
    for (const query of employeeDetailsQueries) {
      if (query.data) details.set(query.data.id, query.data);
    }
    if (selectedDetailQuery.data) {
      details.set(selectedDetailQuery.data.id, selectedDetailQuery.data);
    }
    return details;
  }, [employeeDetailsQueries, selectedDetailQuery.data]);

  const roleOptions = useMemo(() => {
    const roleKeys = new Set(defaultRoleFilters);
    for (const role of rolesQuery.data ?? []) {
      roleKeys.add(role.role_key);
    }
    return Array.from(roleKeys).sort((a, b) => a.localeCompare(b));
  }, [rolesQuery.data]);

  const filteredEmployees = useMemo(() => {
    const normalizedSearch = normalize(search);
    return employees.filter((employee) => {
      const detail = detailsByEmployeeId.get(employee.id);
      const matchesSearch =
        normalizedSearch.length === 0 ||
        normalize(employee.full_name).includes(normalizedSearch) ||
        normalize(employee.pos_alias).includes(normalizedSearch) ||
        normalize(employee.employee_code).includes(normalizedSearch);
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && employee.active) ||
        (statusFilter === "inactive" && !employee.active);
      const matchesRole =
        roleFilter === "all" ||
        Boolean(detail?.roles.some((role) => role.role_key === roleFilter));
      const matchesPin =
        pinFilter === "all" ||
        (pinFilter === "enabled" && detail?.pin_enabled === true) ||
        (pinFilter === "disabled" && detail?.pin_enabled === false);

      return matchesSearch && matchesStatus && matchesRole && matchesPin;
    });
  }, [detailsByEmployeeId, employees, pinFilter, roleFilter, search, statusFilter]);

  const knownDetails = Array.from(detailsByEmployeeId.values());
  const protectedQueries = [
    rolesQuery,
    permissionsQuery,
    selectedDetailQuery,
    selectedPermissionsQuery,
    ...employeeDetailsQueries,
  ];
  const protectedAccessDenied = protectedQueries.some(
    (query) => query.isError && isAccessDenied(query.error),
  );
  const protectedHasError = protectedQueries.some((query) => query.isError);
  const protectedIsLoading = protectedQueries.some((query) => query.isFetching);
  const selectedEmployee = employees.find((employee) => employee.id === selectedEmployeeId);
  const selectedDetail =
    selectedDetailQuery.data ??
    (selectedEmployeeId !== null ? detailsByEmployeeId.get(selectedEmployeeId) : undefined);
  const selectedDialogHasError = selectedDetailQuery.isError || selectedPermissionsQuery.isError;
  const selectedDialogAccessDenied =
    isAccessDenied(selectedDetailQuery.error) || isAccessDenied(selectedPermissionsQuery.error);
  const isRefreshing = employeesQuery.isFetching || protectedIsLoading;

  function refreshAll() {
    const protectedRefetches = sessionToken
      ? [
          rolesQuery.refetch(),
          permissionsQuery.refetch(),
          ...employeeDetailsQueries.map((query) => query.refetch()),
        ]
      : [];
    const selectedRefetches =
      sessionToken && selectedEmployeeId !== null
        ? [selectedDetailQuery.refetch(), selectedPermissionsQuery.refetch()]
        : [];

    void Promise.all([
      employeesQuery.refetch(),
      ...protectedRefetches,
      ...selectedRefetches,
    ]);
  }

  const totalEmployees = employees.length;
  const activeEmployees = employees.filter((employee) => employee.active).length;
  const inactiveEmployees = totalEmployees - activeEmployees;
  const pinEnabledCount = knownDetails.filter((detail) => detail.pin_enabled).length;
  const pinDisabledCount = knownDetails.filter((detail) => !detail.pin_enabled).length;
  const pinKpiBlocked = protectedAccessDenied || !sessionToken;
  const pinKpiLoading = protectedIsLoading && knownDetails.length < employees.length;

  return (
    <div className="grid gap-4">
      <header className="flex flex-wrap items-center justify-between gap-4 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard)]">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.2em] text-[var(--kp-selected)]">
            Administración
          </p>
          <h1 className="mt-1 text-3xl font-black uppercase md:text-5xl">Empleados</h1>
          <p className="mt-2 max-w-2xl text-sm font-bold text-[var(--kp-muted)]">
            Revisa accesos, roles y permisos del personal.
          </p>
        </div>
        <BrutalButton onClick={refreshAll} disabled={isRefreshing}>
          <RefreshCw className="h-5 w-5" /> Actualizar
        </BrutalButton>
      </header>

      {employeesQuery.isPending ? (
        <LoadingState />
      ) : employeesQuery.isError ? (
        <ErrorState
          title="No se pudo cargar Empleados"
          message={
            isAccessDenied(employeesQuery.error)
              ? "No tienes permiso para ver esta información."
              : "Intenta de nuevo."
          }
        />
      ) : (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <KpiTile label="Total empleados" value={totalEmployees} />
            <KpiTile label="Activos" value={activeEmployees} />
            <KpiTile label="Inactivos" value={inactiveEmployees} />
            <KpiTile
              label="Con PIN activo"
              value={pinKpiBlocked ? "-" : pinKpiLoading ? "..." : pinEnabledCount}
            />
            <KpiTile
              label="Sin PIN"
              value={pinKpiBlocked ? "-" : pinKpiLoading ? "..." : pinDisabledCount}
            />
          </section>

          {protectedAccessDenied || !sessionToken ? (
            <ErrorState
              title="Acceso restringido"
              message="No tienes permiso para ver esta información."
            />
          ) : protectedHasError ? (
            <ErrorState
              title="No se pudo cargar información de accesos"
              message="Intenta de nuevo."
            />
          ) : null}

          <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard-sm)]">
            <div className="grid gap-3 lg:grid-cols-[minmax(220px,1fr)_160px_180px_160px]">
              <label className="grid gap-1 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                Buscar
                <span className="flex items-center gap-2 border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3">
                  <Search className="h-4 w-4 text-[var(--kp-text)]" />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Nombre, alias o código"
                    className="min-h-[var(--kp-touch-md)] w-full bg-transparent text-sm font-bold normal-case tracking-normal text-[var(--kp-text)] outline-none placeholder:text-[var(--kp-muted)]"
                  />
                </span>
              </label>

              <label className="grid gap-1 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                Estado
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
                  className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-sm font-black uppercase text-[var(--kp-text)]"
                >
                  <option value="all">Todos</option>
                  <option value="active">Activos</option>
                  <option value="inactive">Inactivos</option>
                </select>
              </label>

              <label className="grid gap-1 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                Rol
                <select
                  value={roleFilter}
                  onChange={(event) => setRoleFilter(event.target.value)}
                  className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-sm font-black uppercase text-[var(--kp-text)]"
                >
                  <option value="all">Todos</option>
                  {roleOptions.map((roleKey) => (
                    <option key={roleKey} value={roleKey}>
                      {roleKey}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-1 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
                PIN
                <select
                  value={pinFilter}
                  onChange={(event) => setPinFilter(event.target.value as PinFilter)}
                  className="min-h-[var(--kp-touch-md)] border-4 border-[var(--kp-ink)] bg-[var(--kp-surface-raised)] px-3 text-sm font-black uppercase text-[var(--kp-text)]"
                >
                  <option value="all">Todos</option>
                  <option value="enabled">PIN activo</option>
                  <option value="disabled">Sin PIN</option>
                </select>
              </label>
            </div>

            <p className="mt-3 text-xs font-black uppercase tracking-[0.12em] text-[var(--kp-muted)]">
              Mostrando {filteredEmployees.length} de {employees.length}
            </p>
          </section>

          <EmployeeList
            employees={filteredEmployees}
            detailsByEmployeeId={detailsByEmployeeId}
            selectedEmployeeId={selectedEmployeeId}
            onViewDetail={setSelectedEmployeeId}
          />

          <SystemRolesPanel
            roles={rolesQuery.data ?? []}
            permissions={permissionsQuery.data ?? []}
            isLoading={rolesQuery.isFetching || permissionsQuery.isFetching}
            hasError={rolesQuery.isError || permissionsQuery.isError}
            accessDenied={isAccessDenied(rolesQuery.error) || isAccessDenied(permissionsQuery.error)}
          />

          <section className="border-4 border-[var(--kp-ink)] bg-[var(--kp-surface)] p-4 shadow-[var(--kp-shadow-hard-sm)]">
            <p className="text-xs font-black uppercase tracking-[0.18em] text-[var(--kp-selected)]">
              Pendiente de habilitar
            </p>
            <h2 className="mt-1 text-xl font-black uppercase">Cambios de acceso</h2>
            <p className="mt-2 text-sm font-bold text-[var(--kp-muted)]">
              Crear empleados, cambiar PIN y modificar roles requiere habilitar edición
              administrativa.
            </p>
            <p className="mt-2 text-sm font-black uppercase">
              Disponible después de activar administración de empleados.
            </p>
          </section>
        </>
      )}

      {selectedEmployee ? (
        <EmployeeDetailDialog
          employee={selectedEmployee}
          detail={selectedDetail}
          employeePermissions={selectedPermissionsQuery.data}
          isLoading={selectedDetailQuery.isFetching || selectedPermissionsQuery.isFetching}
          hasError={selectedDialogHasError}
          accessDenied={selectedDialogAccessDenied}
          onClose={() => setSelectedEmployeeId(null)}
        />
      ) : null}
    </div>
  );
}
