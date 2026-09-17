import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';

import ComoDecideScreen from '../screens/info/ComoDecideScreen';
import DisponibilidadScreen from '../screens/manage/DisponibilidadScreen';
import EventosScreen from '../screens/manage/EventosScreen';
import HabitosScreen from '../screens/manage/HabitosScreen';
import ObjetivosScreen from '../screens/manage/ObjetivosScreen';
import TareasScreen from '../screens/manage/TareasScreen';
import AjustesScreen from '../screens/settings/AjustesScreen';
import type { AjustesStackParamList } from './types';

const Stack = createNativeStackNavigator<AjustesStackParamList>();

/**
 * Ajustes ahora es un stack, no una pantalla suelta: además de la cuenta,
 * es el punto de entrada a gestionar tareas/eventos/objetivos/
 * disponibilidad (petición de Daniel de completar el CRUD que faltaba del
 * Módulo 5). Sin header nativo — cada pantalla hija usa BackHeader, mismo
 * patrón "a mano" que el resto de la app.
 */
export default function AjustesStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="AjustesHome" component={AjustesScreen} />
      <Stack.Screen name="Tareas" component={TareasScreen} />
      <Stack.Screen name="Eventos" component={EventosScreen} />
      <Stack.Screen name="Objetivos" component={ObjetivosScreen} />
      <Stack.Screen name="Disponibilidad" component={DisponibilidadScreen} />
      <Stack.Screen name="Habitos" component={HabitosScreen} />
      <Stack.Screen name="ComoDecide" component={ComoDecideScreen} />
    </Stack.Navigator>
  );
}
