import { appConfig } from "@/config/app-config";
import { login, LoginResponse } from "@/lib/auth"; // Giả sử hàm login này cho Credentials
import axiosServer from "@/lib/axios/server"; // Sử dụng axios server instance của bạn
import {
  NextAuthOptions,
  User as NextAuthUser,
  Account,
  Profile,
  User,
} from "next-auth"; // Import các kiểu cần thiết
import { JWT } from "next-auth/jwt"; // Import kiểu JWT
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import GitHubProvider from "next-auth/providers/github";
import AzureADProvider from "next-auth/providers/azure-ad";

// Định nghĩa kiểu AuthProvider để nhất quán với backend
type AuthProvider = "google" | "github" | "azure-ad"; // Thêm các provider khác nếu có

export const AUTH_OPTIONS: NextAuthOptions = {
  secret: appConfig.nextAuthSecret, // Rất quan trọng!
  providers: [
    // Google OAuth
    GoogleProvider({
      clientId: appConfig.googleClientId,
      clientSecret: appConfig.googleClientSecret,
      // PKCE được dùng mặc định
    }),
    // GitHub OAuth
    GitHubProvider({
      clientId: appConfig.githubClientId,
      clientSecret: appConfig.githubClientSecret,
      // PKCE được dùng mặc định
    }),
    // Microsoft Azure AD OAuth
    AzureADProvider({
      clientId: appConfig.microsoftClientId,
      clientSecret: appConfig.microsoftClientSecret,
      tenantId: appConfig.microsoftTenantId,
      authorization: {
        params: {
          // offline_access để lấy refresh_token (nếu cần)
          // openid, email, profile là các scope OIDC chuẩn
          scope: "openid email profile offline_access",
        },
      },
      // PKCE được dùng mặc định
    }),
    // Credentials Provider (Giữ nguyên nếu bạn vẫn cần)
    CredentialsProvider({
      name: "credentials",
      type: "credentials",
      credentials: {
        email: { label: "Email", type: "text", placeholder: "Email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials): Promise<User | null> {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        try {
          // Gọi hàm login API của bạn (có thể là endpoint khác của FastAPI)
          const data = await login(credentials.email, credentials.password);
          // Tạo đối tượng User cho NextAuth
          // Lưu ý: accessToken ở đây nên là FastAPI token nếu hàm login trả về nó
          const user: User = {
            id: data.user.id, // ID từ hệ thống của bạn
            email: data.user.email,
            name: data.user.username, // Hoặc full_name tùy ý
            accessToken: data.accessToken, // FastAPI token
          };
          return user;
        } catch (error) {
          console.error("Credentials login failed:", error);
          return null; // Trả về null nếu authorize thất bại
        }
      },
    }),
  ],
  session: {
    strategy: "jwt", // Bắt buộc dùng JWT để tùy chỉnh token và session
  },
  callbacks: {
    /**
     * Callback này được gọi khi JWT được tạo (lần đầu đăng nhập) hoặc cập nhật.
     * Nó chạy *trước* callback `session`.
     * Chúng ta sẽ gọi FastAPI tại đây để lấy token nội bộ.
     */
    async jwt({
      token,
      user,
      account,
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
      const isCredentials = account?.provider === "credentials"; // Kiểm tra provider credentials

      console.log(
        `JWT Callback: isSignIn=${isSignIn}, Provider=${account?.provider}`
      );
      // console.log("JWT token in:", token);
      // console.log("User in:", user);
      // console.log("Account in:", account);

      // --- Xử lý đăng nhập bằng Credentials ---
      if (isSignIn && isCredentials && user) {
        console.log("Handling Credentials sign-in...");
        // User đã chứa FastAPI token từ hàm authorize
        const extendedUser = user as User;
        token.accessToken = extendedUser.accessToken; // Lưu FastAPI token
        token.sub = extendedUser.id; // Đặt subject là ID hệ thống
        token.email = extendedUser.email;
        token.name = extendedUser.name;
        token.picture = extendedUser.image; // Nếu có
        console.log("Stored FastAPI token from Credentials user into JWT.");
        return token;
      }

      // --- Xử lý đăng nhập bằng OAuth Provider ---
      if (isSignIn && account && !isCredentials) {
        console.log(
          `Handling OAuth sign-in for provider: ${account.provider}...`
        );
        const provider = account.provider as AuthProvider;

        // Chuẩn bị payload để gửi đến FastAPI
        const backendPayload: {
          provider: AuthProvider;
          id_token?: string | null;
          access_token?: string | null;
        } = {
          provider: provider,
          id_token: null,
          access_token: null,
        };

        if (
          (provider === "google" || provider === "azure-ad") &&
          account.id_token
        ) {
          backendPayload.id_token = account.id_token;
          console.log(`Prepared payload with ID Token for ${provider}`);
        } else if (provider === "github" && account.access_token) {
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
                "Content-Type": "application/json",
              },
            }
          );

          const { accessToken, user: user2 } = res.data;

          console.log("FastAPI response:", res.data);

          // Kiểm tra response từ FastAPI

          if (res.status === 200 && accessToken) {
            console.log(
              "FastAPI verification successful. Storing FastAPI token."
            );

            const tokenUser: User = {
              id: user2.email,
              email: user2.email,
              name: user2.username,
              image: "", // Có thể thêm ảnh nếu cần
              accessToken: accessToken, // Lưu access token từ FastAPI vào token
            };
            token.user = tokenUser;
          }
          console.log("Stored FastAPI token and user info into NextAuth JWT.");
        } catch (error) {
          throw error;
        }
      }

      // Trả về token đã được cập nhật (hoặc token cũ nếu không phải lần đăng nhập đầu)
      // console.log("JWT token out:", token);
      return token;
    },

    /**
     * Callback này được gọi sau callback `jwt`, dùng để tạo đối tượng `session`
     * mà frontend (useSession, getServerSession) có thể truy cập.
     */
    async session({ session, token }) {
      if (session?.user) {
        Object.assign(session.user, token.user);
      }

      return session;
    },
  },
  pages: {
    signIn: "/login", // Trang đăng nhập tùy chỉnh của bạn
    // error: '/auth/error', // Trang hiển thị lỗi tùy chỉnh (tùy chọn)
  },
};

const handler = NextAuth(AUTH_OPTIONS);

export { handler as GET, handler as POST };
