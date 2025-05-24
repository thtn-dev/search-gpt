import { appConfig } from '@/config/app-config';
import { login, LoginResponse } from '@/lib/auth';
// Giả sử hàm login này cho Credentials
import axiosServer from '@/lib/axios/server';
// Sử dụng axios server instance của bạn
import {
  NextAuthOptions,
  User as NextAuthUser,
  Account,
  Profile,
  User
} from 'next-auth';
// Import kiểu JWT
import NextAuth from 'next-auth';
// Import các kiểu cần thiết
import { JWT } from 'next-auth/jwt';
import AzureADProvider from 'next-auth/providers/azure-ad';
import CredentialsProvider from 'next-auth/providers/credentials';
import GitHubProvider from 'next-auth/providers/github';
import GoogleProvider from 'next-auth/providers/google';

type AuthProvider = 'google' | 'github' | 'azure-ad';

export const AUTH_OPTIONS: NextAuthOptions = {
  secret: appConfig.nextAuthSecret,
  providers: [
    // Google OAuth
    GoogleProvider({
      clientId: appConfig.googleClientId,
      clientSecret: appConfig.googleClientSecret
    }),
    // GitHub OAuth
    GitHubProvider({
      clientId: appConfig.githubClientId,
      clientSecret: appConfig.githubClientSecret
    }),
    // Microsoft Azure AD OAuth
    AzureADProvider({
      clientId: appConfig.microsoftClientId,
      clientSecret: appConfig.microsoftClientSecret,
      tenantId: appConfig.microsoftTenantId,
      authorization: {
        params: {
          scope: 'openid email profile offline_access'
        }
      }
    }),
    CredentialsProvider({
      name: 'credentials',
      type: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'text', placeholder: 'Email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        try {
          const data = await login(credentials.email, credentials.password);
          const user: User = {
            id: data.user.id,
            email: data.user.email,
            name: data.user.username,
            accessToken: data.access_token
          };
          return user;
        } catch (error) {
          throw error;
        }
      }
    })
  ],
  debug: true,
  session: {
    strategy: 'jwt'
  },
  callbacks: {
    async jwt({
      token,
      user,
      account
    }: {
      token: JWT;
      user?: NextAuthUser | User;
      account?: Account | null;
      profile?: Profile;
    }): Promise<JWT> {
      // `token` là JWT hiện tại của NextAuth.
      // `user` là đối tượng user trả về từ provider hoặc hàm authorize (chỉ có khi đăng nhập lần đầu).
      // `account` chứa thông tin từ provider (access_token, id_token, provider...) (chỉ có khi đăng nhập lần đầu).
      // `profile` chứa thông tin user profile từ provider (chỉ có khi đăng nhập lần đầu với OAuth).
      const isSignIn = !!(user && account); // Kiểm tra xem đây có phải là lần đăng nhập đầu tiên không
      const isCredentials = account?.provider === 'credentials'; // Kiểm tra provider credentials
      // --- Xử lý đăng nhập bằng Credentials ---
      if (isSignIn && isCredentials && user) {
        console.log('Handling Credentials sign-in...');
        // User đã chứa FastAPI token từ hàm authorize
        const extendedUser = user as User;
        token.accessToken = extendedUser.accessToken;
        token.sub = extendedUser.id;
        token.email = extendedUser.email;
        token.name = extendedUser.name;
        token.picture = extendedUser.image; // Nếu có
        console.log('Stored FastAPI token from Credentials user into JWT.');
        return token;
      }

      // --- Xử lý đăng nhập bằng OAuth Provider ---
      if (isSignIn && account && !isCredentials) {
        const provider = account.provider as AuthProvider;

        // Chuẩn bị payload để gửi đến FastAPI
        const backendPayload: {
          provider: AuthProvider;
          id_token?: string | null;
          access_token?: string | null;
        } = {
          provider: provider,
          id_token: null,
          access_token: null
        };

        if (
          (provider === 'google' || provider === 'azure-ad') &&
          account.id_token
        ) {
          backendPayload.id_token = account.id_token;
          console.log(`Prepared payload with ID Token for ${provider}`);
        } else if (provider === 'github' && account.access_token) {
          backendPayload.access_token = account.access_token;
          console.log(`Prepared payload with Access Token for ${provider}`);
        } else {
          console.error(
            `Missing required token (id_token or access_token) for provider ${provider} in account:`,
            account
          );
          throw new Error(`Missing required token for provider ${provider}`);
        }

        try {
          // Gọi đến endpoint FastAPI chung
          console.log(
            `Calling FastAPI endpoint: ${appConfig.apiBaseUrl}/api/v1/auth/nextauth-signin`
          );
          const res = await axiosServer.post<LoginResponse>(
            `${appConfig.apiBaseUrl}/api/v1/auth/nextauth-signin`, // Endpoint FastAPI chung
            backendPayload, // Body chứa provider và token tương ứng
            {
              headers: {
                'Content-Type': 'application/json'
              }
            }
          );

          const { access_token: accessToken, user: user2 } = res.data;
          if (res.status === 200 && accessToken) {
            console.log(
              'FastAPI verification successful. Storing FastAPI token.'
            );

            const tokenUser: User = {
              id: user2.email,
              email: user2.email,
              name: user2.username,
              image: '', // Có thể thêm ảnh nếu cầnJWT token out
              accessToken: accessToken // Lưu access token từ FastAPI vào token
            };
            token.user = tokenUser;
          }
          console.log('Stored FastAPI token and user info into NextAuth JWT.');
        } catch (error) {
          throw error;
        }
      }

      return token;
    },

    /**
     * Callback này được gọi sau callback `jwt`, dùng để tạo đối tượng `session`
     * mà frontend (useSession, getServerSession) có thể truy cập.
     */
    async session({ session, token }) {
      if (session?.user) {
        session.user.id = token.sub as string; // ID từ hệ thống của bạn
        session.user.email = token.email as string; // Email từ token
        session.user.accessToken = token.accessToken as string; // FastAPI token
        session.user.name = token.name as string; // Tên từ token
      }
      return session;
    }
  },
  pages: {
    signIn: '/login',
    signOut: '/login'
  }
};

const handler = NextAuth(AUTH_OPTIONS);

export { handler as GET, handler as POST };
