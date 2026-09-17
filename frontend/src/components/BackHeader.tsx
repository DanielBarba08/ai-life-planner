import { Ionicons } from '@expo/vector-icons';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';

/**
 * Encabezado con botón de regreso para las pantallas de gestión que se
 * abren dentro de AjustesStack (Tareas, Eventos, Objetivos,
 * Disponibilidad) — el resto de la app no usa el header nativo de
 * navegación en ningún lado (ver OnboardingNavigator/AuthNavigator,
 * headerShown: false siempre), así que esto sigue el mismo patrón de
 * título "a mano" en vez de mezclar dos estilos de header.
 */
export function BackHeader({ title, onBack }: { title: string; onBack: () => void }) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        row: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg },
        backBtn: {
          width: 34,
          height: 34,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        title: { ...type.h1, color: color.ink },
      }),
    [color]
  );

  return (
    <View style={styles.row}>
      <Pressable style={styles.backBtn} onPress={onBack} hitSlop={8} testID="back-button">
        <Ionicons name="chevron-back" size={20} color={color.accent} />
      </Pressable>
      <Text style={styles.title}>{title}</Text>
    </View>
  );
}
