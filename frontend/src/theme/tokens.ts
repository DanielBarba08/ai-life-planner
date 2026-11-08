/**
 * Sistema de diseño de la app — identidad visual "naturaleza/bienestar"
 * pedida por Daniel (6 nov): verde bosque, verde salvia, verde oliva,
 * beige cálido, arena, café, terracota suave y blanco cálido, en vez de
 * la paleta teal/navy anterior. Reemplaza SOLO los valores de color de
 * este archivo — toda la app (incluida la barra lateral) ya leía sus
 * colores de aquí vía `useTheme()`, así que el cambio de identidad visual
 * es enteramente de este archivo hacia afuera, sin tocar un solo
 * componente ni pantalla. Tipografía real vía @expo-google-fonts (ver
 * App.tsx: useFonts), sin cambios.
 *
 * Los 8 colores exactos que dio Daniel se usan tal cual donde se puede
 * (fondo, superficies, botones principales, menú lateral); los estados
 * semánticos (good/warn/risk/streak) usan una versión más oscura de la
 * misma familia de color cuando el tono "suave" original no daba
 * suficiente contraste como texto — verificado con la fórmula de
 * contraste WCAG, no a ojo (ver pares fg/Soft abajo, todos ≥4.5:1).
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

  // Menú lateral (ver components/Sidebar.tsx) — chrome de marca SIEMPRE
  // oscuro/navy, igual en ambas paletas (mismo patrón que heroGradient*
  // abajo): el mockup de Daniel muestra una barra lateral oscura fija, no
  // una que cambie con el tema claro/oscuro de la app.
  sidebarBg: string;
  sidebarBorder: string;
  sidebarInk: string;
  sidebarMuted: string;
  sidebarActiveBg: string;
  sidebarAccent: string;
}

export const lightColor: ColorTokens = {
  bg: '#F4EBDD', // beige cálido
  surface: '#FFFCF7', // blanco cálido — tarjetas
  surfaceAlt: '#DCCBB1', // arena — superficies secundarias (chips, círculos de ícono)
  line: '#E8DCC6', // borde sutil entre beige y arena
  ink: '#3A2B1C', // café oscurecido — texto principal (13.3:1 sobre blanco cálido)
  muted: '#795B40', // café — texto secundario e íconos (6.1:1 sobre blanco cálido)

  accent: '#35452F', // verde bosque — botones principales y acción (8.7:1 sobre el fondo)
  accentDark: '#283620', // hover/pressed y texto sobre accentSoft
  accentInk: '#FFFCF7', // blanco cálido — texto/ícono sobre accent
  accentSoft: '#E3E8DD', // tinte muy claro de verde bosque

  // Semánticos: misma familia natural pero cada uno con suficiente
  // contraste como texto sobre su propio *Soft (≥4.5:1, verificado con la
  // fórmula WCAG) — nunca el tono "suave" puro de la paleta de marca
  // directamente como texto, que se lava sobre fondos claros.
  good: '#4F6244', // verde salvia oscurecido — también el color de las barras de progreso
  goodSoft: '#E3EADB',
  warn: '#8C5F1C', // dorado mostaza, de la familia de la terracota
  warnSoft: '#F5E6C4',
  risk: '#9C4A32', // terracota-rojizo
  riskSoft: '#F3DCCC',

  danger: '#C1442B',

  // Racha diaria (sección de diseño: enganche) — terracota suave
  // oscurecida para que el texto de los bloques de "descanso" (ver
  // kindStyle en WeekCalendarGrid.tsx) se lea bien; el tono exacto de
  // marca (#D9A15F) se reserva para acentos grandes/íconos (sidebarAccent
  // abajo), donde no hace falta el mismo contraste de texto chico.
  streak: '#8F5A26',
  streakSoft: '#F7E2C4',

  // Extremos del degradado de la tarjeta hero de Mi día (ver Hero.tsx) —
  // deliberadamente IGUALES en las dos paletas: una tarjeta de acento
  // vivo se lee bien tanto sobre fondo claro como oscuro (mismo patrón
  // que las tarjetas de color de Duolingo), así que no hace falta una
  // segunda pareja de valores solo para el modo oscuro.
  heroGradientStart: '#35452F', // verde bosque
  heroGradientEnd: '#71845B', // verde salvia

  // Menú lateral — verde bosque fijo en ambas paletas (ver el comentario
  // de ColorTokens arriba): "barra lateral: verde bosque" pedido tal cual.
  sidebarBg: '#35452F',
  sidebarBorder: '#28351F',
  sidebarInk: '#FFFCF7', // blanco cálido
  sidebarMuted: '#B9C2AC', // verde oliva aclarado, legible sobre el bosque (5.6:1)
  sidebarActiveBg: 'rgba(217,161,95,0.22)', // terracota suave translúcida
  sidebarAccent: '#D9A15F', // terracota suave — tono de marca exacto, aquí sí como acento/ícono
};

export const darkColor: ColorTokens = {
  bg: '#161D13',
  surface: '#1F2A19',
  surfaceAlt: '#28351F',
  line: '#36462A',
  ink: '#F4EBDD', // beige cálido como texto — espejo del fondo claro
  muted: '#B9AE94',

  accent: '#8FA876', // verde oliva/salvia aclarado — el verde bosque saturado pierde contraste sobre fondo oscuro
  accentDark: '#C9D9B4', // texto/ícono sobre accentSoft oscuro — el "dark" de la pareja es el más CLARO de los dos, a propósito
  accentInk: '#1E2616', // café muy oscuro — texto sobre el accent claro
  accentSoft: '#2C3722',

  good: '#9BB37E',
  goodSoft: '#28331F',
  warn: '#D9AE5C',
  warnSoft: '#3B2E13',
  risk: '#D98F6E',
  riskSoft: '#3B2013',

  danger: '#E08468',

  streak: '#D9A15F', // aquí sí el tono de marca exacto — el fondo oscuro le da suficiente contraste
  streakSoft: '#3B2C13',

  heroGradientStart: '#35452F',
  heroGradientEnd: '#71845B',

  sidebarBg: '#35452F',
  sidebarBorder: '#28351F',
  sidebarInk: '#FFFCF7',
  sidebarMuted: '#B9C2AC',
  sidebarActiveBg: 'rgba(217,161,95,0.22)',
  sidebarAccent: '#D9A15F',
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
    shadowColor: '#2A2118', // café muy oscuro, no el navy de la paleta anterior
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 3,
    elevation: 1,
  },
  card: {
    shadowColor: '#2A2118',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 3,
  },
  raised: {
    shadowColor: '#28351F', // verde bosque oscuro — sombra de la tarjeta hero/menú, antes era azul
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.2,
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
