import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';

import {
  ColorTokens,
  ElevationTokens,
  darkColor,
  darkElevation,
  evidenceLevelColorFor,
  lightColor,
  lightElevation,
} from './tokens';

/**
 * Fuente única de la paleta activa. Sigue la preferencia del sistema por
 * defecto (`useColorScheme()`), con override manual guardado en
 * AsyncStorage (mismo patrón "wrapper simple" que src/api/storage.ts, sin
 * capa extra de abstracción) — así el toggle en Ajustes sobrevive a cerrar
 * la app. `color`/`elevation` que entrega el hook YA son la paleta correcta
 * para el modo activo: ningún componente decide claro/oscuro por su cuenta.
 */

export type ThemeMode = 'system' | 'light' | 'dark';

const MODE_KEY = 'ailp.theme_mode';

interface ThemeContextValue {
  color: ColorTokens;
  elevation: ElevationTokens;
  evidenceLevelColor: Record<string, { fg: string; bg: string }>;
  isDark: boolean;
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useColorScheme();
  const [mode, setModeState] = useState<ThemeMode>('system');

  useEffect(() => {
    AsyncStorage.getItem(MODE_KEY).then((saved) => {
      if (saved === 'light' || saved === 'dark' || saved === 'system') setModeState(saved);
    });
  }, []);

  const setMode = (next: ThemeMode) => {
    setModeState(next);
    AsyncStorage.setItem(MODE_KEY, next);
  };

  const isDark = mode === 'system' ? systemScheme === 'dark' : mode === 'dark';

  const value = useMemo<ThemeContextValue>(() => {
    const c = isDark ? darkColor : lightColor;
    const e = isDark ? darkElevation : lightElevation;
    return { color: c, elevation: e, evidenceLevelColor: evidenceLevelColorFor(c), isDark, mode, setMode };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDark, mode]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/** Único punto de entrada a la paleta activa — nunca importar `lightColor`/`darkColor` sueltos fuera de aquí. */
export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme() debe usarse dentro de <ThemeProvider>');
  return ctx;
}
