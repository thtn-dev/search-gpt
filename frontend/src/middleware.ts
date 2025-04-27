import { NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
    const token = await getToken({
      req: request,
      secret: "WSOeGdcuWv2Y7Var0uegasIr7x8wgWUBRrDhAnm4C48=",
    });
  
    const isAuthenticated = !!token;
    const isAuthPage = request.nextUrl.pathname.startsWith("/login");
  
    if (!isAuthenticated && !isAuthPage) {
      // Lưu lại url hiện tại để chuyển hướng sau khi đăng nhập
      const url = new URL(`/login`, request.url);
      url.searchParams.set("callbackUrl", request.nextUrl.pathname);
      return NextResponse.redirect(url);
    }
  
    if (isAuthenticated && isAuthPage) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  
    return NextResponse.next();
  }
  
  // Chỉ áp dụng middleware cho các route này
  export const config = {
    matcher: [
      "/chat", 
      "/login"
    ],
  };