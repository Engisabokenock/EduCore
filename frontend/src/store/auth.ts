/**
 * Auth store — JWT tokens and current user, persisted via cookies.
 */
import { create } from "zustand";
import Cookies from "js-cookie";
import api from "@/lib/api";
import type { User, AuthTokens } from "@/types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (tokens: AuthTokens, user: User) => void;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: false,
  isAuthenticated: !!Cookies.get("access_token"),

  login(tokens, user) {
    Cookies.set("access_token", tokens.access, { secure: true, sameSite: "lax", expires: 1 / 24 });
    Cookies.set("refresh_token", tokens.refresh, { secure: true, sameSite: "lax", expires: 7 });
    set({ user, isAuthenticated: true });
  },

  async logout() {
    try {
      const refresh = Cookies.get("refresh_token");
      if (refresh) await api.post("/auth/logout/", { refresh });
    } catch {}
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
    set({ user: null, isAuthenticated: false });
  },

  async fetchMe() {
    if (!Cookies.get("access_token")) return;
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
