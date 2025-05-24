export { default } from 'next-auth/middleware';
// Chỉ áp dụng middleware cho các route này
export const config = {
  matcher: ['/chat/:path*', '/dashboard/:path*']
};
