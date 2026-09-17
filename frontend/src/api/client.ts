import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

import { clearTokens, getTokens, setTokens } from './storage';

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

export const api = axios.create({ baseURL: API_URL });

// El resto de la app se entera de una sesión muerta (refresh también
// expiró o fue revocado) suscribiéndose aquí — así AuthContext puede
// limpiar el estado y mandar de vuelta a Login sin que este archivo tenga
// que saber nada de React/navegación.
type UnauthorizedHandler = () => void;
let onUnauthorized: UnauthorizedHandler | null = null;
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null) {
  onUnauthorized = handler;
}

api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const { access } = await getTokens();
  if (access) {
    config.headers.set('Authorization', `Bearer ${access}`);
  }
  return config;
});

// Evita que dos 401 simultáneos disparen dos refrescos a la vez.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = await getTokens();
  if (!refresh) return null;
  try {
    // /v1/auth/refresh solo devuelve un access_token nuevo — el backend usa
    // refresh tokens sin estado (ver backend/README.md), así que el mismo
    // refresh token se sigue usando hasta que expire (30 días).
    const { data } = await axios.post(`${API_URL}/v1/auth/refresh`, { refresh_token: refresh });
    await setTokens(data.access_token, refresh);
    return data.access_token as string;
  } catch {
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retried?: boolean }) | undefined;
    const status = error.response?.status;

    if (status === 401 && original && !original._retried && !original.url?.includes('/v1/auth/')) {
      original._retried = true;
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const newAccess = await refreshPromise;
      if (newAccess) {
        original.headers.set('Authorization', `Bearer ${newAccess}`);
        return api(original);
      }
      await clearTokens();
      onUnauthorized?.();
    }
    return Promise.reject(error);
  }
);

/** Mensaje legible desde un error de axios contra este backend (siempre {"detail": "..."}). */
export function apiErrorMessage(err: unknown, fallback = 'Algo salió mal. Intenta de nuevo.'): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  }
  return fallback;
}
