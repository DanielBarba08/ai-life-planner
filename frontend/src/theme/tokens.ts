/**
 * Sistema de diseño de la app — paleta azul/blanco pedida por Daniel
 * (18 sept: "colores de tonos azules con blanco... atractiva al público
 * ... pero que al mismo tiempo se vea profesional"), con tipografía real
 * cargada vía @expo-google-fonts (ver App.tsx: useFonts) en vez de las
 * fuentes del sistema que se usaron en la primera versión del Módulo 5.
 *
 * Tema oscuro completo (pedido por Daniel como mejora de pulido, no parte
 * del MVP original): DOS paletas con las mismas claves (`lightColor` /
 * `darkColor`, `lightElevation` / `darkElevation`) — nunca una sola
 * paleta mutable, porque `StyleSheet.create` congela los valores que
 * recibe en el momento en que se llama. Cuál paleta está activa lo decide
 * `src/theme/ThemeContext.tsx` (sigue la preferencia del sistema por
 * defecto, con override manual guardado) y se consume con el hook
 * `useTheme()`, nunca importando `color`/`elevation` sueltos de este
 * archivo — por eso NO se exportan como antes. `spacing`, `radius`,
 * `font` y `type` sí se quedan aquí tal cual: son independientes del
 * tema, no cambian entre claro/oscuro.
 */

/**
 * Interfaz explícita (no `typeof lightColor` con `as const`) a propósito:
 * con `as const`, TypeScript infiere cada valor como su literal exacto
 * (`'#F5F8FF'`), así que `darkColor: typeof lightColor` exigiría que CADA
 * color oscuro fuera textualmente idéntico al claro — lo contrario de lo
 * que buscamos. Declarando la forma como `string`/`number` sueltos, ambas
 * paletas comparten estructura sin compartir valores.
 */
export interface ColorTokens {
  bg: string;
  surface: string;
  surfaceAlt: string;
  line: string;
  ink: string;
  muted: string;
  accent: string;
  accentDark: string;
  accentInk: string;
  accentSoft: string;
  good: string;
  goodSoft: string;
  warn: string;
  warnSoft: string;
  risk: string;
  riskSoft: string;
  danger: string;
  streak: string;
  streakSoft: string;
  heroGradientStart: string;
  heroGradientEnd: string;
}

export const lightColor: ColorTokens = {
  bg: '#F5F8FF',
  surface: '#FFFFFF',
  surfaceAlt: '#EAF1FE',
  line: '#DCE6F7',
  ink: '#0F1E3D',
  muted: '#5C6B8A',

  accent: '#1E4FD8', // azul primario — acción principal
  accentDark: '#15369C', // hover/pressed y texto sobre accentSoft
  accentInk: '#FFFFFF',
  accentSoft: '#E3ECFE',

  // Semánticos: se mantienen distintos del azul a propósito — son señales
  // de significado (nivel de evidencia, confianza, conflictos), no
  // decoración, y perderían claridad si todo fuera azul.
  good: '#146C43',
  goodSoft: '#E1F3E7',
  warn: '#8A5A00',
  warnSoft: '#FCEED2',
  risk: '#9C3B2E',
  riskSoft: '#FBE4DF',

  danger: '#C6362B',

  // Racha diaria (sección de diseño: enganche): naranja/ámbar cálido a
  // propósito — es la única señal "caliente" en una paleta fría, así el
  // ojo la encuentra sola en el encabezado de Mi día sin competir con el
  // azul de acción. Mismo patrón que usan apps de hábitos (Duolingo,
  // Fitbit) para su indicador de racha.
  streak: '#C2540A',
  streakSoft: '#FCE7D3',

  // Extremos del degradado de la tarjeta hero de Mi día (ver Hero.tsx) —
  // deliberadamente IGUALES en las dos paletas: una tarjeta de acento
  // vivo se lee bien tanto sobre fondo claro como oscuro (mismo patrón
  // que las tarjetas de color de Duolingo), así que no hace falta una
  // segunda pareja de valores solo para el modo oscuro.
  heroGradientStart: '#1E4FD8',
  heroGradientEnd: '#3E6BEF',
};

export const darkColor: ColorTokens = {
  bg: '#0A0F1E',
  surface: '#131B2E',
  surfaceAlt: '#1B2540',
  line: '#28324D',
  ink: '#EAF0FF',
  muted: '#8C9BC4',

  accent: '#5C87FF', // más claro que el azul primario del modo claro — el saturado original pierde contraste sobre fondo oscuro
  accentDark: '#B9CBFF', // texto/ícono sobre accentSoft oscuro — el "dark" de la pareja ahora es el más CLARO de los dos, a propósito
  accentInk: '#FFFFFF',
  accentSoft: '#1E2C52',

  good: '#4ADE80',
  goodSoft: '#123422',
  warn: '#F0C24B',
  warnSoft: '#3A2B0C',
  risk: '#F2897C',
  riskSoft: '#3A1913',

  danger: '#F2685C',

  streak: '#FF9A4D',
  streakSoft: '#3A2410',

  heroGradientStart: '#1E4FD8',
  heroGradientEnd: '#3E6BEF',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 20,
  xl: 28,
  pill: 999,
} as const;

/**
 * Profundidad sutil (sombras) para que las tarjetas se sientan "levantadas"
 * de la página en vez de solo bordeadas — parte del estilo "híbrido
 * productivo" pedido por Daniel (Things 3 / Fantastical), no sombras
 * pesadas tipo material design. `elevation` es la propiedad que Android
 * necesita además de shadow*; en iOS y web basta con shadow*.
 *
 * En modo oscuro una sombra NEGRA es invisible sobre un fondo ya oscuro
 * (`darkColor.bg`) — así que `darkElevation` no es la misma sombra con
 * otro color, es un enfoque distinto: una sombra casi nula + un borde de
 * 1px con `darkColor.line` (ver el uso de `elevation` junto con
 * `borderWidth`/`borderColor` en cada componente) para que la tarjeta
 * siga leyéndose "levantada" sin depender de una sombra que no se ve.
 */
interface ShadowPreset {
  shadowColor?: string;
  shadowOffset?: { width: number; height: number };
  shadowOpacity?: number;
  shadowRadius?: number;
  elevation?: number;
}

export interface ElevationTokens {
  none: ShadowPreset;
  low: ShadowPreset;
  card: ShadowPreset;
  raised: ShadowPreset;
}

export const lightElevation: ElevationTokens = {
  none: {},
  low: {
    shadowColor: '#0F1E3D',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 1,
  },
  card: {
    shadowColor: '#0F1E3D',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  raised: {
    shadowColor: '#15369C',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 24,
    elevation: 8,
  },
};

export const darkElevation: ElevationTokens = {
  none: {},
  low: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.4,
    shadowRadius: 3,
    elevation: 1,
  },
  card: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 3,
  },
  raised: {
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.6,
    shadowRadius: 28,
    elevation: 8,
  },
};

/**
 * Manrope para títulos (geométrica, segura, de aire "producto" — no
 * decorativa al punto de restar seriedad) e Inter para texto de lectura
 * (el estándar de facto para UI profesional, muy legible en tamaños
 * chicos). Cada peso es una familia de fuente distinta porque así
 * funcionan las fuentes de Google Fonts en React Native — no un solo
 * "fontWeight" numérico sobre una familia variable.
 */
export const font = {
  displayFamily: 'Manrope_800ExtraBold',
  h1Family: 'Manrope_700Bold',
  h2Family: 'Manrope_700Bold',
  bodyStrongFamily: 'Inter_600SemiBold',
  bodyFamily: 'Inter_400Regular',
  captionFamily: 'Inter_500Medium',
} as const;

export const type = {
  display: { fontFamily: font.displayFamily, fontSize: 30, letterSpacing: -0.4 },
  h1: { fontFamily: font.h1Family, fontSize: 22 },
  h2: { fontFamily: font.h2Family, fontSize: 17 },
  body: { fontFamily: font.bodyFamily, fontSize: 15 },
  bodyStrong: { fontFamily: font.bodyStrongFamily, fontSize: 15 },
  caption: { fontFamily: font.captionFamily, fontSize: 12, letterSpacing: 0.2 },
  mono: { fontSize: 12, fontFamily: 'monospace' as const },
};

/** Nivel de evidencia (sólida/moderada/limitada) → color, para la paleta activa. Reemplaza la constante fija que había antes — ver ThemeContext.tsx. */
export function evidenceLevelColorFor(color: ColorTokens): Record<string, { fg: string; bg: string }> {
  return {
    solida: { fg: color.good, bg: color.goodSoft },
    moderada: { fg: color.warn, bg: color.warnSoft },
    limitada: { fg: color.risk, bg: color.riskSoft },
  };
}
