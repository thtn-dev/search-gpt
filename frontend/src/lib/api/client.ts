'use client';

import axios, { AxiosInstance, AxiosResponse } from 'axios';

// Extend AxiosInstance to include custom methods
declare module 'axios' {
  export interface AxiosInstance {
    setAuthToken: (token: string) => void;
    clearAuthToken: () => void;
  }
}

// Extend Axios config to include metadata
declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    metadata?: {
      startTime: number;
    };
  }
}

// Base Axios client configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    },
    // Performance optimizations
    maxRedirects: 5,
    maxContentLength: 50 * 1024 * 1024, // 50MB
    maxBodyLength: 50 * 1024 * 1024, // 50MB
    validateStatus: (status) => status >= 200 && status < 300
  });

  // Token management
  let authToken: string | null = null;

  const setAuthToken = (token: string) => {
    authToken = token;
    client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  };

  const clearAuthToken = () => {
    authToken = null;
    delete client.defaults.headers.common['Authorization'];
  };

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add request ID for tracking
      config.metadata = { startTime: Date.now() };

      // Add auth token if available
      if (authToken && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${authToken}`;
      }

      // Request logging in development
      if (process.env.NODE_ENV === 'development') {
        console.log(
          `🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`
        );
      }

      return config;
    },
    (error) => {
      console.error('Request interceptor error:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Performance logging
      const duration =
        Date.now() - (response.config.metadata?.startTime || Date.now());
      if (process.env.NODE_ENV === 'development') {
        console.log(
          `✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url} (${duration}ms)`
        );
      }

      return response;
    },
    async (error) => {
      const originalRequest = error.config;

      // Token refresh logic
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken) {
            const response = await client.post('/auth/refresh', {
              refreshToken
            });

            const newToken = response.data.accessToken;
            setAuthToken(newToken);
            localStorage.setItem('accessToken', newToken);

            // Retry original request
            return client(originalRequest);
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError);
          clearAuthToken();
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');

          // Redirect to login or emit event
          window.dispatchEvent(new CustomEvent('auth:logout'));
        }
      }

      // Error logging
      if (process.env.NODE_ENV === 'development') {
        console.error('❌ API Error:', {
          method: error.config?.method,
          url: error.config?.url,
          status: error.response?.status,
          message: error.response?.data?.message || error.message
        });
      }

      return Promise.reject(error);
    }
  );

  // Attach helper methods
  client.setAuthToken = setAuthToken;
  client.clearAuthToken = clearAuthToken;

  return client;
};

export const apiClient = createApiClient();
