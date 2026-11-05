/**
 * Auth token cookie helpers (single place that knows cookie names and flags).
 *
 * `secure` is only set on HTTPS: browsers other than Chrome drop Secure cookies on
 * http://localhost, which made login silently fail in local development.
 */
import Cookies from "js-cookie";
import type { AuthTokens } from "@/types";
import { PORTAL_COOKIE, type Portal } from "@/lib/portal";

export const ACCESS_COOKIE = "access_token";
export const REFRESH_COOKIE = "refresh_token";

const ACCESS_TTL_DAYS = 1 / 24; // 1 hour; the JWT itself expires sooner and is refreshed
const REFRESH_TTL_DAYS = 7;

function cookieOptions(expires: number): Cookies.CookieAttributes {
  const secure = typeof window !== "undefined" && window.location.protocol === "https:";
  return { secure, sameSite: "lax", expires, path: "/" };
}

export function getAccessToken(): string | undefined {
  return Cookies.get(ACCESS_COOKIE);
}

export function getRefreshToken(): string | undefined {
  return Cookies.get(REFRESH_COOKIE);
}

export function setAuthCookies(tokens: AuthTokens): void {
  Cookies.set(ACCESS_COOKIE, tokens.access, cookieOptions(ACCESS_TTL_DAYS));
  Cookies.set(REFRESH_COOKIE, tokens.refresh, cookieOptions(REFRESH_TTL_DAYS));
}

/** UI routing hint read by the Next.js middleware. Not a security boundary: the API is. */
export function setPortalCookie(portal: Portal): void {
  Cookies.set(PORTAL_COOKIE, portal, cookieOptions(REFRESH_TTL_DAYS));
}

export function getPortalCookie(): Portal | undefined {
  const value = Cookies.get(PORTAL_COOKIE);
  return value === "staff" || value === "learner" ? value : undefined;
}

export function clearAuthCookies(): void {
  Cookies.remove(ACCESS_COOKIE, { path: "/" });
  Cookies.remove(REFRESH_COOKIE, { path: "/" });
  Cookies.remove(PORTAL_COOKIE, { path: "/" });
}
