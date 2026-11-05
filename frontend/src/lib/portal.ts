/**
 * Sign-in portals.
 *
 * Students and parents use the public pages (/login, /register, /dashboard).
 * Teachers, administrators and the Super Admin use the staff portal (/staff/login,
 * /teacher, /admin). The API enforces the split; this module only routes the UI.
 */
import type { UserRole } from "@/types";

export type Portal = "learner" | "staff";

export const STAFF_ROLES: readonly UserRole[] = ["teacher", "admin", "super_admin", "school_admin"];

export const PORTAL_COOKIE = "educore_portal";

export function portalFor(role: UserRole | string | undefined | null): Portal {
  return role && (STAFF_ROLES as readonly string[]).includes(role) ? "staff" : "learner";
}

export function isStaffRole(role: UserRole | string | undefined | null): boolean {
  return portalFor(role) === "staff";
}

/** Landing page after sign-in, or when someone opens the wrong area. */
export function homeFor(role: UserRole | string | undefined | null): string {
  switch (role) {
    case "super_admin":
      return "/admin/super";
    case "admin":
      return "/admin";
    case "teacher":
    case "school_admin":
      return "/teacher";
    default:
      return "/dashboard";
  }
}

export function loginPathFor(portal: Portal): string {
  return portal === "staff" ? "/staff/login" : "/login";
}

/** Only allow same-site relative redirects that belong to the user's own portal. */
export function safeRedirect(target: string | null, role: UserRole | string): string {
  if (!target || !target.startsWith("/") || target.startsWith("//")) return homeFor(role);
  const staffArea = target.startsWith("/admin") || target.startsWith("/teacher");
  return staffArea === isStaffRole(role) ? target : homeFor(role);
}
