import axios, {
  type AxiosInstance,
  type AxiosError,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

const API_URL = import.meta.env.VITE_API_URL as string;

/**
 * Base axios instance pointed at the API Gateway.
 * Automatically attaches Bearer token from localStorage on every request.
 * Handles 401 responses by clearing tokens and redirecting to login.
 */
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetryableRequest extends AxiosRequestConfig {
  _retry?: boolean;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequest;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        _clearTokensAndRedirect();
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post<{ access: string }>(
          `${API_URL}/api/auth/token/refresh/`,
          { refresh: refreshToken },
        );
        localStorage.setItem("access_token", data.access);

        if (originalRequest.headers) {
          originalRequest.headers["Authorization"] = `Bearer ${data.access}`;
        }

        return api(originalRequest);
      } catch {
        _clearTokensAndRedirect();
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

function _clearTokensAndRedirect(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_id");
  window.location.href = "/login";
}

export default api;
