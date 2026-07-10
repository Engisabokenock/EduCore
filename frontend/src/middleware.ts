import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/dashboard", "/downloads", "/checkout", "/premium", "/admin"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PROTECTED.some((route) => pathname.startsWith(route))) {
    const token = request.cookies.get("access_token")?.value;
    if (!token) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/downloads/:path*", "/checkout/:path*", "/premium/:path*", "/admin/:path*"],
};
