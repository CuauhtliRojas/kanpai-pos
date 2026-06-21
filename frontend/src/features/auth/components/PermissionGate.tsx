import type { ReactNode } from "react";
import { useAuthSession } from "../hooks/useAuthSession";
import { hasAllPermissions, hasAnyPermission } from "../lib/permissions";
import type { PermissionKey } from "../types/authTypes";

type PermissionGateProps = {
  children: ReactNode;
  anyOf?: readonly PermissionKey[];
  allOf?: readonly PermissionKey[];
  fallback?: ReactNode;
};

export function PermissionGate({
  children,
  anyOf = [],
  allOf = [],
  fallback = null,
}: PermissionGateProps) {
  const { permissions } = useAuthSession();
  const meetsAnyRequirement = anyOf.length === 0 || hasAnyPermission(permissions, anyOf);
  const meetsAllRequirements = hasAllPermissions(permissions, allOf);

  return meetsAnyRequirement && meetsAllRequirements ? children : fallback;
}
