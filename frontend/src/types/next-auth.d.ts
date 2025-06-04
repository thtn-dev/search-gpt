import { DefaultUser, DefaultSession } from 'next-auth';
import { DefaultJWT } from 'next-auth/jwt';

declare module 'next-auth' {
  interface Session extends DefaultSession {
    user: User;
    accessToken: string;
    refreshToken: string;
  }
  interface User extends DefaultUser {
    accessToken?: string;
    refreshToken?: string;
  }
}

declare module 'next-auth/jwt' {
  interface JWT extends DefaultJWT {
    user: User;
    accessToken: string;
    refreshToken: string;
  }
}
