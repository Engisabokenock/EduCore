/**
 * Centralized browser API client for EduCore.
 * All client-side API calls go through here — never call fetch/axios in components.
 *
 * Uses a relative baseURL so requests go through the Next.js rewrite in
 * next.config.js (same-origin, no CORS in production).
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { clearAuthCookies, getAccessToken, getRefreshToken, setAuthCookies } from "@/lib/auth-cookies";

const API_PREFIX = "/api/v1";

const api: AxiosInstance = axios.create({
  baseURL: API_PREFIX,
  headers: { "Content-Type": "application/json" },
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Endpoints where a 401 means "bad credentials", not "expired session".
const NO_REFRESH_PATHS = ["/auth/login", "/auth/register", "/auth/token/refresh", "/auth/refresh", "/auth/logout"];

// Single in-flight refresh shared by every request that failed with 401. The backend
// rotates refresh tokens (each one is single-use), so parallel refreshes would revoke
// each other and log the user out.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;
  try {
    const { data } = await axios.post<{ access: string; refresh: string }>(
      `${API_PREFIX}/auth/token/refresh/`,
      { refresh },
    );
    setAuthCookies({ access: data.access, refresh: data.refresh });
    return data.access;
  } catch {
    clearAuthCookies();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const url = original?.url ?? "";
    const shouldRefresh =
      error.response?.status === 401 &&
      original &&
      !original._retry &&
      !NO_REFRESH_PATHS.some((p) => url.includes(p));

    if (!shouldRefresh) return Promise.reject(error);

    original._retry = true;
    refreshPromise = refreshPromise ?? refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
    const newAccess = await refreshPromise;
    if (!newAccess) {
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login?redirect=${next}`;
      }
      return Promise.reject(error);
    }
    original.headers.Authorization = `Bearer ${newAccess}`;
    return api(original);
  },
);

/** Human-readable message from any API error (backend envelope: { success, error, detail }). */
export function getApiErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  const err = error as AxiosError<{ error?: string; detail?: unknown; message?: string }>;
  if (err?.code === "ECONNABORTED") return "The request timed out. Check your connection and try again.";
  if (err?.response === undefined && err?.request) return "Cannot reach EduCore right now. Check your connection.";
  const data = err?.response?.data;
  if (typeof data?.error === "string") return data.error;
  if (typeof data?.detail === "string") return data.detail;
  if (typeof data?.message === "string") return data.message;
  return fallback;
}

export default api;
