/**
 * Auth store — current user plus JWT tokens persisted in cookies.
 */
import { create } from "zustand";
import api from "@/lib/api";
import { clearAuthCookies, getAccessToken, getRefreshToken, setAuthCookies } from "@/lib/auth-cookies";
import type { User, AuthTokens } from "@/types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (tokens: AuthTokens, user: User) => void;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: false,
  // Cookies can include a refresh token only (access expired) — still a live session.
  isAuthenticated: typeof window !== "undefined" && !!(getAccessToken() || getRefreshToken()),

  login(tokens, user) {
    setAuthCookies(tokens);
    set({ user, isAuthenticated: true });
  },

  async logout() {
    try {
      const refresh = getRefreshToken();
      if (refresh) await api.post("/auth/logout/", { refresh });
    } catch {
      // Logging out locally must succeed even if the API is unreachable.
    }
    clearAuthCookies();
    set({ user: null, isAuthenticated: false });
  },

  async fetchMe() {
    if (!getAccessToken() && !getRefreshToken()) {
      set({ user: null, isAuthenticated: false });
      return;
    }
    set({ isLoading: true });
    try {
      const { data } = await api.get<User>("/auth/me/");
      set({ user: data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
}));
