'use server';

import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import axiosServer from '../axios/server';

export type AppUser = {
  id: string;
  email: string;
  username: string;
};

export type LoginResponse = {
  access_token: string;
  user: AppUser;
};

export async function login(email: string, password: string) {
  try {
    const res = await axiosServer.post<LoginResponse>('/api/v1/auth/login', {
      email,
      password
    });
    const data = res.data;
    return data;
  } catch (error) {
    // check if error is an AxiosError
    if (axios.isAxiosError(error)) {
      // Handle the error response from the server
      const errorMessage = error.response?.data?.detail || 'An error occurred';
      throw new Error(errorMessage);
    } else {
      // Handle other types of errors (e.g., network errors)
      throw new Error('An unexpected error occurred. Please try again.');
    }
  }
}

export async function logout() {
  (await cookies()).delete('token');
  redirect('/login');
}

export async function getUser(): Promise<AppUser | null> {
  const token = (await cookies()).get('token');

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
    redirect('/login');
  }

  return user;
}
