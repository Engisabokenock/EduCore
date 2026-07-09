/**
 * Centralized API client for EduCore Platform.
 * All API calls go through here — never call fetch/axios directly in components.
 *
 * IMPORTANT: Uses a relative baseURL so requests go through Next.js rewrites
 * defined in next.config.js. This avoids CORS issues in production because
 * the browser sees same-origin requests to /api/v1/... and Next.js proxies
 * them to the Railway backend.
 */
import axios, { AxiosError, AxiosInstance } from "axios";
import Cookies from "js-cookie";

// Relative API prefix: Next.js rewrites /api/:path* to the real backend.
const API_PREFIX = "/api/v1";

const api: AxiosInstance = axios.create({
  baseURL: API_PREFIX,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean };
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = Cookies.get("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_PREFIX}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          Cookies.set("access_token", data.access, { secure: true, sameSite: "lax" });
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${data.access}`;
          }
          return api(originalRequest);
        } catch {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
