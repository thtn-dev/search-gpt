import { appConfig } from "@/config/app-config";
import { login, LoginResponse } from "@/lib/auth";
import axiosServer from "@/lib/axios/server";
import { NextAuthOptions, User } from "next-auth";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from 'next-auth/providers/google';
import GitHubProvider from "next-auth/providers/github";
import AzureADProvider from "next-auth/providers/azure-ad";

export const AUTH_OPTIONS: NextAuthOptions = {
  secret: appConfig.nextAuthSecret,
  providers: [
    // Google OAuth
    GoogleProvider({
      clientId: appConfig.googleClientId,
      clientSecret: appConfig.googleClientSecret,
    }),
    // GitHub OAuth 
    GitHubProvider({
      clientId: appConfig.githubClientId,
      clientSecret: appConfig.githubClientSecret,
    }),
    // Microsoft Azure AD OAuth
    AzureADProvider({
      clientId: appConfig.microsoftClientId,
      clientSecret: appConfig.microsoftClientSecret,
      tenantId: appConfig.microsoftTenantId,
      authorization: {
        params: {
          scope: "openid email offline_access",
        },
      },
    }),
    // Credentials Provider
    CredentialsProvider({
      name: "credentials",
      type: "credentials",
      credentials: {
        email: {
          label: "Email",
          type: "text",
          placeholder: "Email",
        },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        const data = await login(credentials.email, credentials.password);
        const user: User = {
          id: data.user.email,
          email: data.user.email,
          name: data.user.username,
          image: "",
          accessToken: data.accessToken,
        };
        return user;
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, account , profile }) {

      console.log('user', user)
      console.log('account', account)
      console.log('profile', profile)

      if (account && user && account.provider === "google"){
        console.log("Initial Google Sign-in, calling FastAPI...");
        const googleIdToken = account.id_token; 
        if (!googleIdToken) {
          console.error("Google ID Token not found in account details.");
          throw new Error("Google ID Token missing");
        }
        try {
          // Gọi đến endpoint FastAPI đã tạo
          const res = await axiosServer.post<LoginResponse>(
            `${appConfig.apiBaseUrl}/api/v1/auth/google/verify-token`,
            { google_id_token: googleIdToken }, // Body của request
            {
              headers: {
                'Content-Type': 'application/json',
              }
            }
          );
          const {accessToken, user : user2} = res.data;
          console.log("FastAPI response:", res.data);
          console.log(profile);
          // Kiểm tra response từ FastAPI
          if (res.status === 200 && accessToken) {
            console.log("FastAPI verification successful. Storing FastAPI token.");
            const tokenUser: User = {
              id: user2.email,
              email: user2.email,
              name: user2.username,
              image: "", // Có thể thêm ảnh nếu cần
              accessToken: accessToken, // Lưu access token từ FastAPI vào token
            }
            token.user = tokenUser; // Gán thông tin người dùng từ FastAPI vào token
          } else {
            console.error("FastAPI verification failed:", res.status, res.data);
            // Không trả về token nếu FastAPI báo lỗi -> đăng nhập thất bại
            // Hoặc có thể throw error để NextAuth báo lỗi rõ ràng hơn
             throw new Error(`FastAPI verification failed with status: ${res.status}`);
            // return null; // Hoặc return null để hủy session
          }
        } catch (error) {
          console.error("Error calling FastAPI backend:", error);
          // Ném lỗi để NextAuth biết quá trình đăng nhập thất bại
          throw new Error("Failed to communicate with backend authentication service");
          // return null; // Hoặc return null
        }
        return token;
      }
      if (user) {
        token.user = user;
      }
       if (account) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      if (session?.user) {
        Object.assign(session.user, token.user);
      }
      return session;
    },

  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
  },
};

const handler = NextAuth(AUTH_OPTIONS);

export { handler as GET, handler as POST };
