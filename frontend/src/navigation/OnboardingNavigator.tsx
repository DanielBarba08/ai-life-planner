import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';

import OnboardingAvailabilityScreen from '../screens/onboarding/OnboardingAvailabilityScreen';
import OnboardingPreferencesScreen from '../screens/onboarding/OnboardingPreferencesScreen';
import OnboardingScheduleScreen from '../screens/onboarding/OnboardingScheduleScreen';
import OnboardingSummaryScreen from '../screens/onboarding/OnboardingSummaryScreen';
import type { OnboardingStackParamList } from './types';

const Stack = createNativeStackNavigator<OnboardingStackParamList>();

export default function OnboardingNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Horario" component={OnboardingScheduleScreen} />
      <Stack.Screen name="Preferencias" component={OnboardingPreferencesScreen} />
      <Stack.Screen name="Disponibilidad" component={OnboardingAvailabilityScreen} />
      <Stack.Screen name="Resumen" component={OnboardingSummaryScreen} />
    </Stack.Navigator>
  );
}
