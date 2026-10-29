import { useWindowDimensions } from 'react-native';

/**
 * A partir de este ancho (px) la app se considera "pantalla ancha"
 * (web/escritorio con mouse, tablet en horizontal) — es donde aparece el
 * menú lateral (ver components/Sidebar.tsx) en vez de la barra de
 * pestañas inferior, y donde Mi día pasa a layout de dos columnas. Un
 * solo punto de quiebre compartido por toda la app para que nada cambie
 * de opinión a medio camino (pedido de Daniel: rediseño con menú lateral
 * en pantallas anchas, barra inferior en el teléfono).
 */
export const WIDE_BREAKPOINT = 860;

export function useIsWideScreen(): boolean {
  const { width } = useWindowDimensions();
  return width >= WIDE_BREAKPOINT;
}
