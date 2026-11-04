import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/dashboard", "/downloads", "/checkout", "/premium", "/admin"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PROTECTED.some((route) => pathname.startsWith(route))) {
    // A refresh token alone is still a valid session: the client refreshes on first call.
    const hasSession =
      request.cookies.has("access_token") || request.cookies.has("refresh_token");
    if (!hasSession) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname + request.nextUrl.search);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/downloads/:path*", "/checkout/:path*", "/premium/:path*", "/admin/:path*"],
};
