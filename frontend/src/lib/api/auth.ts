import axiosClient from '../axios/client';

export const AuthApi = {
  async ping(): Promise<string> {
    const res = await axiosClient.post<string>('/v1/users/ping');
    return res.data;
  },
  async register(user: {
    email: string;
    password: string;
    username: string;
  }): Promise<void> {
    const res = await axiosClient.post('/v1/auth/register', user);
    return res.data;
  }
};
