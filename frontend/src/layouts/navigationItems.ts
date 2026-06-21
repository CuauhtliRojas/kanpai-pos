import {
  BarChart3,
  Boxes,
  CircleDollarSign,
  ClipboardList,
  DatabaseZap,
  Home,
  Printer,
  ReceiptText,
  ShieldCheck,
  Utensils,
  type LucideIcon,
} from "lucide-react";
import {
  hasAllPermissions,
  hasAnyPermission,
  hasRole,
} from "../features/auth/lib/permissions";
import type { PermissionKey } from "../features/auth/types/authTypes";

export type NavigationItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  status: "available" | "coming_soon";
  anyPermission?: readonly PermissionKey[];
  allPermissions?: readonly PermissionKey[];
  adminOnly?: boolean;
};

export type NavigationItemAccess = "available" | "coming_soon" | "denied";

export const navigationItems: readonly NavigationItem[] = [
  { to: "/", label: "Inicio", icon: Home, status: "available" },
  { to: "/system", label: "Estado", icon: DatabaseZap, status: "available" },
  {
    to: "/cash",
    label: "Caja",
    icon: CircleDollarSign,
    status: "available",
    anyPermission: ["CASH_SHIFT_OPEN", "CASH_SHIFT_CLOSE", "EXPENSE_CREATE"],
  },
  { to: "/pos", label: "POS", icon: ReceiptText, status: "available" },
  { to: "/production", label: "Producción", icon: Utensils, status: "available" },
  {
    to: "/printing",
    label: "Impresión",
    icon: Printer,
    status: "available",
  },
  {
    to: "/inventory",
    label: "Inventario",
    icon: Boxes,
    status: "available",
  },
  { to: "/reports", label: "Reportes", icon: BarChart3, status: "available", adminOnly: true },
  { to: "/audit", label: "Auditoría", icon: ClipboardList, status: "available", adminOnly: true },
  { to: "/security", label: "Permisos", icon: ShieldCheck, status: "available", adminOnly: true },
];

export function resolveNavigationItemAccess(
  item: NavigationItem,
  roles: readonly string[],
  permissions: readonly string[],
): NavigationItemAccess {
  if (item.status === "coming_soon") return "coming_soon";
  if (item.adminOnly && !hasRole(roles, "ADMIN")) return "denied";
  if (item.anyPermission && !hasAnyPermission(permissions, item.anyPermission)) return "denied";
  if (item.allPermissions && !hasAllPermissions(permissions, item.allPermissions)) return "denied";
  return "available";
}
