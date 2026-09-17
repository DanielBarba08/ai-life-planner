import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { ColorTokens, radius, type } from '../theme/tokens';

export function Pill({ label, fg, bg }: { label: string; fg: string; bg: string }) {
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        pill: {
          paddingHorizontal: 10,
          paddingVertical: 4,
          borderRadius: radius.pill,
          alignSelf: 'flex-start',
        },
        text: { ...type.caption, textTransform: 'uppercase' },
      }),
    []
  );
  return (
    <View style={[styles.pill, { backgroundColor: bg }]}>
      <Text style={[styles.text, { color: fg }]}>{label}</Text>
    </View>
  );
}

export const confidenceLabel: Record<string, string> = { alta: 'Confianza alta', media: 'Confianza media', baja: 'Confianza baja' };

/** Antes era una constante fija atada a la paleta clara — ahora recibe la paleta activa (ver ThemeContext.tsx), igual que evidenceLevelColorFor en tokens.ts. */
export function confidenceColorFor(color: ColorTokens): Record<string, { fg: string; bg: string }> {
  return {
    alta: { fg: color.good, bg: color.goodSoft },
    media: { fg: color.warn, bg: color.warnSoft },
    baja: { fg: color.muted, bg: color.surfaceAlt },
  };
}
