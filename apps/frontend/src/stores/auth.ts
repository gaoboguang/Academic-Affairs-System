import { defineStore } from "pinia";

import { apiRequest } from "../api/client";
import { setCsrfToken } from "../api/authSession";

export type UserRole = "admin" | "teacher";

export interface AppUser {
  id: number;
  username: string;
  display_name: string;
  role: UserRole;
  teacher_id?: number | null;
  teacher_name?: string | null;
  must_change_password: boolean;
  extra_class_ids: number[];
  effective_class_ids: number[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthPayload {
  user: AppUser;
  permissions: string[];
  csrf_token: string;
}

export interface AdminUserCreatePayload {
  username: string;
  display_name: string;
  role: UserRole;
  teacher_id?: number | null;
  extra_class_ids: number[];
}

export interface AdminUserUpdatePayload {
  display_name: string;
  role: UserRole;
  teacher_id?: number | null;
  extra_class_ids: number[];
  is_active: boolean;
}

export interface AdminUserCreateResponse {
  user: AppUser;
  temporary_password: string;
}

interface AuthState {
  user: AppUser | null;
  permissions: string[];
  initialized: boolean;
}

function applyAuthPayload(state: AuthState, payload: AuthPayload): void {
  state.user = payload.user;
  state.permissions = payload.permissions;
  setCsrfToken(payload.csrf_token);
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    user: null,
    permissions: [],
    initialized: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    isAdmin: (state) => state.user?.role === "admin",
    mustChangePassword: (state) => Boolean(state.user?.must_change_password),
    hasPermission: (state) => (permission?: string): boolean => {
      if (!permission) return true;
      if (state.permissions.includes("admin:*")) return true;
      return state.permissions.includes(permission);
    },
  },
  actions: {
    async fetchCurrentUser(): Promise<void> {
      try {
        const payload = await apiRequest<AuthPayload>("/api/auth/me");
        applyAuthPayload(this, payload);
      } catch {
        this.user = null;
        this.permissions = [];
        setCsrfToken(null);
      } finally {
        this.initialized = true;
      }
    },
    async login(username: string, password: string): Promise<void> {
      const payload = await apiRequest<AuthPayload>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      applyAuthPayload(this, payload);
      this.initialized = true;
    },
    async logout(): Promise<void> {
      await apiRequest<{ message: string }>("/api/auth/logout", { method: "POST" }).catch(() => ({ message: "" }));
      this.user = null;
      this.permissions = [];
      this.initialized = true;
      setCsrfToken(null);
    },
    async changePassword(currentPassword: string, newPassword: string): Promise<void> {
      const payload = await apiRequest<AuthPayload>("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      applyAuthPayload(this, payload);
    },
  },
});
