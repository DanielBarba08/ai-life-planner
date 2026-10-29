import { Ionicons } from '@expo/vector-icons';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import React from 'react';

import AsistenteScreen from '../screens/assistant/AsistenteScreen';
import MiDiaScreen from '../screens/day/MiDiaScreen';
import MiSemanaScreen from '../screens/week/MiSemanaScreen';
import { useTheme } from '../theme/ThemeContext';
import AjustesStack from './AjustesStack';
import type { MainTabParamList } from './types';

const Tab = createBottomTabNavigator<MainTabParamList>();

// Íconos reales (Ionicons, vienen empaquetados con Expo — sin dependencia
// extra) en vez del emoji de la primera versión: se ven consistentes entre
// plataformas/fuentes del sistema operativo y permiten un estado
// activo/inactivo con el mismo ícono relleno vs. contorno, como las apps
// de referencia (Things 3, Fantastical).
const ICONS: Record<keyof MainTabParamList, { active: keyof typeof Ionicons.glyphMap; inactive: keyof typeof Ionicons.glyphMap }> = {
  MiDia: { active: 'sunny', inactive: 'sunny-outline' },
  MiSemana: { active: 'calendar', inactive: 'calendar-outline' },
  Asistente: { active: 'chatbubble-ellipses', inactive: 'chatbubble-ellipses-outline' },
  Ajustes: { active: 'settings', inactive: 'settings-outline' },
};

const LABELS: Record<keyof MainTabParamList, string> = {
  MiDia: 'Mi día',
  MiSemana: 'Mi semana',
  Asistente: 'Asistente',
  Ajustes: 'Ajustes',
};

export default function MainTabs({ hideTabBar }: { hideTabBar?: boolean } = {}) {
  const { color } = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: color.accent,
        tabBarInactiveTintColor: color.muted,
        // hideTabBar: en pantallas anchas la navegación vive en el menú
        // lateral (ver components/Sidebar.tsx + navigation/RootNavigator.tsx)
        // — la barra inferior se oculta para no duplicar la navegación,
        // pero el Tab.Navigator sigue siendo la única fuente de verdad de
        // qué pantalla está activa, en ambos tamaños.
        tabBarStyle: hideTabBar
          ? { display: 'none' }
          : { backgroundColor: color.surface, borderTopColor: color.line, height: 62, paddingBottom: 8, paddingTop: 6 },
        tabBarLabelStyle: { fontSize: 11 },
        tabBarLabel: LABELS[route.name as keyof MainTabParamList],
        tabBarIcon: ({ color: tint, focused }) => {
          const icon = ICONS[route.name as keyof MainTabParamList];
          return <Ionicons name={focused ? icon.active : icon.inactive} size={22} color={tint} />;
        },
      })}
    >
      <Tab.Screen name="MiDia" component={MiDiaScreen} />
      <Tab.Screen name="MiSemana" component={MiSemanaScreen} />
      <Tab.Screen name="Asistente" component={AsistenteScreen} />
      <Tab.Screen name="Ajustes" component={AjustesStack} />
    </Tab.Navigator>
  );
}
