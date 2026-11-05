import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Route guard for the two sign-in portals.
 *
 * - Learner areas (students and parents) send signed-out visitors to /login.
 * - Staff areas (teachers, administrators, Super Admin) send them to /staff/login.
 * - A signed-in user who opens the other portal's area is sent to their own home.
 *
 * The portal cookie is only a routing hint; every API call is authorised server-side.
 */
const LEARNER_AREAS = ["/dashboard", "/downloads", "/checkout", "/premium"];
const STAFF_AREAS = ["/admin", "/teacher"];
const PORTAL_COOKIE = "educore_portal";

function startsWithAny(pathname: string, prefixes: string[]): boolean {
  return prefixes.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const staffArea = startsWithAny(pathname, STAFF_AREAS);
  const learnerArea = startsWithAny(pathname, LEARNER_AREAS);
  if (!staffArea && !learnerArea) return NextResponse.next();

  // A refresh token alone is still a valid session: the client refreshes on first call.
  const hasSession = request.cookies.has("access_token") || request.cookies.has("refresh_token");
  if (!hasSession) {
    const loginUrl = new URL(staffArea ? "/staff/login" : "/login", request.url);
    loginUrl.searchParams.set("redirect", pathname + request.nextUrl.search);
    return NextResponse.redirect(loginUrl);
  }

  const portal = request.cookies.get(PORTAL_COOKIE)?.value;
  if (staffArea && portal === "learner") {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }
  if (learnerArea && portal === "staff") {
    // The staff landing page picks the right home (teacher workspace or admin panel).
    return NextResponse.redirect(new URL("/staff", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/downloads/:path*",
    "/checkout/:path*",
    "/premium/:path*",
    "/admin/:path*",
    "/teacher/:path*",
  ],
};
