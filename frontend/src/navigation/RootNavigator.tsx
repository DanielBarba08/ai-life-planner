import { NavigationContainer, useNavigationContainerRef } from '@react-navigation/native';
import React from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAuth } from '../auth/AuthContext';
import { Sidebar, SidebarDestination } from '../components/Sidebar';
import { useTheme } from '../theme/ThemeContext';
import { useIsWideScreen } from '../utils/layout';
import AuthNavigator from './AuthNavigator';
import MainTabs from './MainTabs';
import OnboardingNavigator from './OnboardingNavigator';

/**
 * Única fuente de verdad de "en qué pantalla debería estar el usuario":
 * sin sesión -> Auth; con sesión pero onboarding_completed=false ->
 * Onboarding; con sesión y onboarding terminado -> las pestañas
 * principales. Ningún botón navega "a mano" entre estos tres mundos —
 * todos pasan por cambiar el estado real (login/registro/PATCH onboarding)
 * y dejan que esto reaccione solo.
 *
 * En pantallas anchas, las pestañas principales se envuelven en el menú
 * lateral (ver components/Sidebar.tsx, pedido por Daniel a partir del
 * mockup de referencia) — mismo Tab.Navigator de siempre, solo que su
 * propia barra inferior se oculta (MainTabs({hideTabBar: true})) y la
 * navegación lateral apunta al mismo árbol vía navigationRef, nunca un
 * navigator paralelo. currentRoute viene de la ruta "hoja" real
 * (getCurrentRoute().name) para que Tareas/Objetivos —que viven dentro
 * del stack de Ajustes, no como tabs propios— también se resalten bien.
 */
export default function RootNavigator() {
  const { user, isLoading } = useAuth();
  const { color } = useTheme();
  const navigationRef = useNavigationContainerRef();
  const [currentRoute, setCurrentRoute] = React.useState<string | undefined>();
  const isWide = useIsWideScreen();

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: color.bg },
        shellRow: { flex: 1, flexDirection: 'row' },
        shellContent: { flex: 1 },
      }),
    [color]
  );

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={color.accent} />
      </View>
    );
  }

  // El tipo que infiere useNavigationContainerRef() sin genérico es `never`
  // para sus parámetros (no hay un único ParamList raíz: el hijo puede ser
  // Auth/Onboarding/MainTabs según el estado) — por eso los *usos* de
  // navigate/getCurrentRoute pasan por este alias `any`, nunca el `ref` que
  // le pasamos a NavigationContainer, que sí debe quedarse con su tipo real.
  const nav = navigationRef as any;

  const handleSidebarNavigate = (dest: SidebarDestination) => {
    if (dest.tab === 'Ajustes') {
      nav.navigate('Ajustes', { screen: dest.screen ?? 'AjustesHome' });
    } else {
      nav.navigate(dest.tab);
    }
  };

  return (
    <NavigationContainer
      ref={navigationRef}
      onReady={() => setCurrentRoute(nav.getCurrentRoute()?.name)}
      onStateChange={() => setCurrentRoute(nav.getCurrentRoute()?.name)}
    >
      {!user ? (
        <AuthNavigator />
      ) : !user.onboarding_completed ? (
        <OnboardingNavigator />
      ) : isWide ? (
        <View style={styles.shellRow}>
          <Sidebar currentRoute={currentRoute} onNavigate={handleSidebarNavigate} />
          <View style={styles.shellContent}>
            <MainTabs hideTabBar />
          </View>
        </View>
      ) : (
        <MainTabs />
      )}
    </NavigationContainer>
  );
}
