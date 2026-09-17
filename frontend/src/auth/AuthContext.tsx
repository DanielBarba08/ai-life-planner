import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { setUnauthorizedHandler } from '../api/client';
import { authApi, usersApi } from '../api/endpoints';
import { clearTokens, getTokens, setTokens } from '../api/storage';
import type { User } from '../api/types';

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string, timezone?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const me = await usersApi.me();
    setUser(me);
  }, []);

  const logout = useCallback(async () => {
    await clearTokens();
    setUser(null);
  }, []);

  useEffect(() => {
    // Si un refresh de token falla de verdad (el refresh también expiró),
    // el cliente HTTP no sabe nada de React — solo avisa por aquí, y
    // AuthContext es quien decide mandar de vuelta a la pantalla de login.
    setUnauthorizedHandler(() => {
      setUser(null);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    (async () => {
      const { access } = await getTokens();
      if (access) {
        try {
          await refreshUser();
        } catch {
          await clearTokens();
        }
      }
      setIsLoading(false);
    })();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await authApi.login({ email, password });
      await setTokens(tokens.access_token, tokens.refresh_token);
      await refreshUser();
    },
    [refreshUser]
  );

  const register = useCallback(
    async (email: string, password: string, name?: string, timezone?: string) => {
      // /v1/auth/register no devuelve tokens (solo crea el usuario) — el
      // flujo real es registrar y después iniciar sesión, igual que se
      // verificó a mano en la demo del backend.
      await authApi.register({ email, password, name, timezone });
      await login(email, password);
    },
    [login]
  );

  const value = useMemo(
    () => ({ user, isLoading, login, register, logout, refreshUser }),
    [user, isLoading, login, register, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>');
  return ctx;
}
