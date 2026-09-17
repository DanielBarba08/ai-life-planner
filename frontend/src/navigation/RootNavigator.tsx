import { NavigationContainer } from '@react-navigation/native';
import React from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../theme/ThemeContext';
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
 */
export default function RootNavigator() {
  const { user, isLoading } = useAuth();
  const { color } = useTheme();
  const styles = React.useMemo(
    () => StyleSheet.create({ loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: color.bg } }),
    [color]
  );

  if (isLoading) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color={color.accent} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      {!user ? <AuthNavigator /> : !user.onboarding_completed ? <OnboardingNavigator /> : <MainTabs />}
    </NavigationContainer>
  );
}
