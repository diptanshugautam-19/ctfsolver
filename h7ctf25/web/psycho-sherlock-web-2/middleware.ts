import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// This function can be marked `async` if using `await` inside
export function middleware(request: NextRequest) {
  // Check if the request is for a forbidden route
  if (request.nextUrl.pathname.startsWith("/forbidden/")) {
    // Redirect to login page if not authenticated
    return NextResponse.redirect(new URL("/forbidden", request.url));
  }

  return NextResponse.next();
}

// Configure which paths this middleware runs on
export const config = {
  matcher: ["/forbidden/:path*"],
};
