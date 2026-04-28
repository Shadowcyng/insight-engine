// src/api/apiClient.ts
import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { $accessToken, setUser } from "@/store/authStore";

interface CustomAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// 1. The Base Client
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost/api/v1",
  withCredentials: true,
});

// Minor comment: Variables to prevent spamming the refresh endpoint if 5 requests fail at once
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

// Minor comment: Helper to process the paused requests once the refresh finishes
const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.request.use((config) => {
  const token = $accessToken.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 2. The Interceptor Logic
apiClient.interceptors.response.use(
  (response) => response, // Minor comment: If the request succeeds, just pass it through
  async (error: AxiosError) => {
    const originalRequest = error.config as CustomAxiosRequestConfig;

    // Minor comment: If error is not 401, or if we already retried this request, reject immediately
    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      (originalRequest as any)._retry
    ) {
      return Promise.reject(error);
    }

    // Minor comment: If we are already refreshing, pause this request and add it to the queue
    if (isRefreshing) {
      return new Promise(function (resolve, reject) {
        failedQueue.push({ resolve, reject });
      })
        .then(() => {
          return apiClient(originalRequest);
        })
        .catch((err) => {
          return Promise.reject(err);
        });
    }

    // Minor comment: Mark this request as retried and lock the refresh state
    originalRequest._retry = true;
    isRefreshing = true;

    try {
      // Minor comment: Call the FastAPI refresh endpoint. HttpOnly cookie is attached automatically.
      const response = await axios.post(
        "http://localhost/api/v1/auth/refresh",
        {},
        { withCredentials: true },
      );
      const { access_token, user } = response.data;
      setUser(user, access_token);
      // Minor comment: If successful, release the queue and retry the original request
      processQueue(null);
      return apiClient(originalRequest);
    } catch (refreshError) {
      // Minor comment: If the refresh token is also expired, the user is completely logged out
      processQueue(refreshError as Error, null);

      // Minor comment: Update Nanostore to instantly kick them to the login screen
      setUser(null);

      return Promise.reject(refreshError);
    } finally {
      // Minor comment: Always unlock the refresh state when done
      isRefreshing = false;
    }
  },
);
