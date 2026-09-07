import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "../api/client";
import type { UserMe } from "../types";

interface AuthContextValue {
  user: UserMe | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  can: (permissionCode: string) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem("sigma_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get<UserMe>("/api/auth/me");
      setUser(data);
    } catch {
      localStorage.removeItem("sigma_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const { data } = await api.post("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("sigma_token", data.access_token);
    await refreshUser();
  };

  const logout = () => {
    localStorage.removeItem("sigma_token");
    setUser(null);
    window.location.href = "/login";
  };

  const can = (permissionCode: string) => {
    if (!user) return false;
    return user.is_superadmin || user.permissions.includes(permissionCode);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth doit être utilisé à l'intérieur d'un <AuthProvider>.");
  return ctx;
}
