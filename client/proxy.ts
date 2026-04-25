import { type NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/register", "/verify-otp", "/forgot-password", "/reset-password", "/share"];
const ONBOARDING_PATH = "/onboarding";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isAuthenticated = Boolean(request.cookies.get("tm_auth")?.value);

  // Allow public assets and Next.js internals through
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  const isPublicPath = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

  // Redirect unauthenticated users trying to access protected pages
  if (!isAuthenticated && !isPublicPath && pathname !== ONBOARDING_PATH) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect already authenticated users away from login/register
  if (isAuthenticated && isPublicPath) {
    return NextResponse.redirect(new URL("/chat", request.url));
  }

  return NextResponse.next();
}

export const config = {
  // Run middleware on all routes except static files
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
