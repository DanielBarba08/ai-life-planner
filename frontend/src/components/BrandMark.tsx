import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import React from 'react';
import { StyleSheet } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing } from '../theme/tokens';

/**
 * Marca visual en Login/Registro — un badge con degradado en vez de solo
 * texto, para que la primera pantalla que alguien ve ya se sienta como un
 * producto pulido y no un formulario genérico. Mismo par de colores que
 * el hero de Mi día (theme/tokens.ts::heroGradient*) para que la identidad
 * visual sea consistente entre la puerta de entrada y la app.
 */
export function BrandMark() {
  const { color, elevation } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        badge: {
          width: 48,
          height: 48,
          borderRadius: radius.md,
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: spacing.md,
        },
      }),
    []
  );

  return (
    <LinearGradient
      colors={[color.heroGradientStart, color.heroGradientEnd]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.badge, elevation.low]}
    >
      <Ionicons name="sunny" size={22} color={color.accentInk} />
    </LinearGradient>
  );
}
