import type { PermissionKey } from "../types/authTypes";

export function hasPermission(
  permissions: readonly string[],
  permission: PermissionKey,
): boolean {
  return permissions.includes(permission);
}

export function hasAnyPermission(
  permissions: readonly string[],
  required: readonly PermissionKey[],
): boolean {
  return required.some((permission) => hasPermission(permissions, permission));
}

export function hasAllPermissions(
  permissions: readonly string[],
  required: readonly PermissionKey[],
): boolean {
  return required.every((permission) => hasPermission(permissions, permission));
}

export function hasRole(roles: readonly string[], role: string): boolean {
  return roles.includes(role);
}
