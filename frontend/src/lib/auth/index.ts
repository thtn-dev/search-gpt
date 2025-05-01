"use server";

import { cookies } from "next/headers";
import { jwtDecode } from "jwt-decode";
import { redirect } from "next/navigation";
import axiosServer from "../axios/server";

export type AppUser = {
  id: string;
  email: string;
  username: string;
};

export type LoginResponse = {
  accessToken: string;
  user: AppUser;
};

export async function login(email: string, password: string) {
  try {
    const res = await axiosServer.post<LoginResponse>("/api/v1/auth/login", {
      email,
      password,
    });
    const data = res.data;
    return data;
  } catch (error) {
    console.log(error);
    throw error;
  }
}

export async function logout() {
  (await cookies()).delete("token");
  redirect("/login");
}

export async function getUser(): Promise<AppUser | null> {
  const token = (await cookies()).get("token");

  if (!token) {
    return null;
  }

  try {
    const decoded = jwtDecode<AppUser>(token.value);
    return decoded;
  } catch {
    return null;
  }
}

export async function requireAuth() {
  const user = await getUser();

  if (!user) {
    redirect("/login");
  }

  return user;
}
