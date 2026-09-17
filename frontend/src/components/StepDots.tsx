import React from 'react';
import { StyleSheet, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing } from '../theme/tokens';

/** Indicador de progreso del onboarding (3 pasos) — refuerzo visual de que
 * falta poco, además del texto "Paso X de 3" que ya tenía cada pantalla. */
export function StepDots({ total, current }: { total: number; current: number }) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        row: { flexDirection: 'row', marginBottom: spacing.sm },
        dot: { height: 4, borderRadius: radius.pill, marginRight: spacing.xs },
        dotActive: { width: 24, backgroundColor: color.accent },
        dotInactive: { width: 12, backgroundColor: color.line },
      }),
    [color]
  );

  return (
    <View style={styles.row}>
      {Array.from({ length: total }).map((_, i) => (
        <View key={i} style={[styles.dot, i + 1 === current ? styles.dotActive : styles.dotInactive]} />
      ))}
    </View>
  );
}
