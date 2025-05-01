import { appConfig } from '@/config/app-config';
import axios from 'axios';
import { getSession } from 'next-auth/react';

// Tạo instance axios với URL base
const axiosClient = axios.create({
  baseURL: appConfig.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Thêm interceptor cho request
axiosClient.interceptors.request.use(
  async (config) => {
    // Lấy session từ NextAuth
    const session = await getSession();
    console.log("session", session);
    // Nếu có token trong session, thêm vào header
    if (session?.user.accessToken) {
      config.headers.Authorization = `Bearer ${session.user.accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Thêm interceptor cho response
axiosClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Nếu lỗi 401 (Unauthorized) và chưa thử refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Ở đây bạn có thể thêm logic refresh token nếu cần
        // Ví dụ: gọi API để refresh token và cập nhật session
        
        // Sau khi refresh, lấy session mới
        const session = await getSession();
        
        // Thực hiện lại request với token mới
        if (session?.user.accessToken) {
          originalRequest.headers.Authorization = `Bearer ${session.user.accessToken}`;
          return axiosClient(originalRequest);
        }
      } catch (refreshError) {
        // Nếu refresh token thất bại, đăng xuất hoặc xử lý phù hợp
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default axiosClient;