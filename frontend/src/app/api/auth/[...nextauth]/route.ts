import { login } from "@/lib/auth";
import { NextAuthOptions, User } from "next-auth";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const AUTH_OPTIONS: NextAuthOptions = {
  secret: "WSOeGdcuWv2Y7Var0uegasIr7x8wgWUBRrDhAnm4C48=",
  providers: [
    CredentialsProvider({
      name: "credentials",
      type: "credentials",
      credentials: {
        username: {
          label: "UserName",
          type: "text",
          placeholder: "Username",
        },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          return null;
        }
        const data = await login(credentials.username, credentials.password);
        const user: User = {
          id: data.user.username,
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
    async jwt({ token, user }) {
      if (user) {
        token.user = user;
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
