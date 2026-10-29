import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';

/**
 * A dónde navega cada ítem del menú lateral. "Ajustes" es el único tab que
 * es en realidad un stack (ver navigation/AjustesStack.tsx) — por eso
 * puede llevar un `screen` nested (Tareas/Objetivos/AjustesHome viven ahí,
 * no como tabs propios, para no tocar MainTabParamList ni la barra
 * inferior del teléfono).
 */
export type SidebarDestination =
  | { tab: 'MiDia' }
  | { tab: 'MiSemana' }
  | { tab: 'Asistente' }
  | { tab: 'Ajustes'; screen?: 'AjustesHome' | 'Tareas' | 'Objetivos' };

interface SidebarItem {
  key: string;
  icon: keyof typeof Ionicons.glyphMap;
  activeIcon: keyof typeof Ionicons.glyphMap;
  label: string;
  dest: SidebarDestination;
  /** Nombres de ruta "hoja" (lo que entrega navigationRef.getCurrentRoute(),
   * ver RootNavigator.tsx) que cuentan como "este ítem está activo". */
  matchRoutes: string[];
}

const ITEMS: SidebarItem[] = [
  { key: 'dia', icon: 'sunny-outline', activeIcon: 'sunny', label: 'Mi día', dest: { tab: 'MiDia' }, matchRoutes: ['MiDia'] },
  {
    key: 'semana',
    icon: 'calendar-outline',
    activeIcon: 'calendar',
    label: 'Calendario',
    dest: { tab: 'MiSemana' },
    matchRoutes: ['MiSemana'],
  },
  {
    key: 'tareas',
    icon: 'checkmark-done-outline',
    activeIcon: 'checkmark-done',
    label: 'Tareas',
    dest: { tab: 'Ajustes', screen: 'Tareas' },
    matchRoutes: ['Tareas'],
  },
  {
    key: 'objetivos',
    icon: 'flag-outline',
    activeIcon: 'flag',
    label: 'Objetivos',
    dest: { tab: 'Ajustes', screen: 'Objetivos' },
    matchRoutes: ['Objetivos'],
  },
  {
    key: 'asistente',
    icon: 'chatbubble-ellipses-outline',
    activeIcon: 'chatbubble-ellipses',
    label: 'Asistente',
    dest: { tab: 'Asistente' },
    matchRoutes: ['Asistente'],
  },
  {
    key: 'ajustes',
    icon: 'settings-outline',
    activeIcon: 'settings',
    label: 'Configuración',
    dest: { tab: 'Ajustes', screen: 'AjustesHome' },
    matchRoutes: ['AjustesHome', 'Eventos', 'Disponibilidad', 'Habitos', 'ComoDecide'],
  },
];

/**
 * Menú lateral para pantallas anchas (ver utils/layout.ts::useIsWideScreen),
 * pedido por Daniel a partir del mockup de referencia ("LifePlanner" +
 * navegación vertical oscura). Vive fuera del Tab.Navigator — no reemplaza
 * la barra inferior, que sigue intacta para el teléfono (ver
 * navigation/MainTabs.tsx) — y navega vía la referencia de navegación que
 * arma RootNavigator.tsx, por eso recibe `onNavigate` en vez de un prop de
 * navigation propio.
 */
export function Sidebar({
  currentRoute,
  onNavigate,
}: {
  currentRoute: string | undefined;
  onNavigate: (dest: SidebarDestination) => void;
}) {
  const { color } = useTheme();
  const { user } = useAuth();
  const initial = (user?.name || user?.email || '?').trim().charAt(0).toUpperCase();

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        wrap: {
          width: 232,
          backgroundColor: color.sidebarBg,
          borderRightWidth: 1,
          borderRightColor: color.sidebarBorder,
          paddingVertical: spacing.lg,
          paddingHorizontal: spacing.md,
          flexDirection: 'column',
        },
        brandRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.xl, paddingHorizontal: spacing.sm },
        brandMark: {
          width: 30,
          height: 30,
          borderRadius: radius.md,
          backgroundColor: color.sidebarAccent,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        brandText: { ...type.h2, color: color.sidebarInk },
        items: { flex: 1 },
        item: {
          flexDirection: 'row',
          alignItems: 'center',
          paddingVertical: 11,
          paddingHorizontal: spacing.sm,
          borderRadius: radius.md,
          marginBottom: 2,
        },
        itemActive: { backgroundColor: color.sidebarActiveBg },
        itemIcon: { marginRight: spacing.sm },
        itemLabel: { ...type.bodyStrong, color: color.sidebarMuted },
        itemLabelActive: { color: color.sidebarInk },
        footer: {
          paddingTop: spacing.md,
          borderTopWidth: 1,
          borderTopColor: color.sidebarBorder,
          flexDirection: 'row',
          alignItems: 'center',
          paddingHorizontal: spacing.sm,
        },
        avatar: {
          width: 28,
          height: 28,
          borderRadius: radius.pill,
          backgroundColor: color.sidebarActiveBg,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        avatarText: { ...type.caption, color: color.sidebarAccent },
        footerText: { ...type.caption, color: color.sidebarMuted, flexShrink: 1 },
      }),
    [color]
  );

  return (
    <View style={styles.wrap}>
      <View style={styles.brandRow}>
        <View style={styles.brandMark}>
          <Ionicons name="sparkles" size={16} color={color.sidebarBg} />
        </View>
        <Text style={styles.brandText}>LifePlanner</Text>
      </View>

      <View style={styles.items}>
        {ITEMS.map((item) => {
          const active = !!currentRoute && item.matchRoutes.includes(currentRoute);
          return (
            <Pressable key={item.key} onPress={() => onNavigate(item.dest)} style={[styles.item, active && styles.itemActive]}>
              <Ionicons
                name={active ? item.activeIcon : item.icon}
                size={18}
                color={active ? color.sidebarAccent : color.sidebarMuted}
                style={styles.itemIcon}
              />
              <Text style={[styles.itemLabel, active && styles.itemLabelActive]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </View>

      <View style={styles.footer}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initial}</Text>
        </View>
        <Text style={styles.footerText} numberOfLines={1}>
          {user?.name || user?.email}
        </Text>
      </View>
    </View>
  );
}
