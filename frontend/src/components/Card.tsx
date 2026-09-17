import React from 'react';
import { StyleProp, StyleSheet, View, ViewStyle } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing } from '../theme/tokens';

export function Card({ children, style }: { children: React.ReactNode; style?: StyleProp<ViewStyle> }) {
  const { color, elevation } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        card: {
          backgroundColor: color.surface,
          borderRadius: radius.lg,
          padding: spacing.md,
          borderWidth: 1,
          borderColor: color.line,
          // Sombra sutil (ver theme/tokens.ts::lightElevation/darkElevation) para
          // que la tarjeta se sienta levantada de la página, no solo delimitada
          // por un borde.
          ...elevation.card,
        },
      }),
    [color, elevation]
  );
  return <View style={[styles.card, style]}>{children}</View>;
}
