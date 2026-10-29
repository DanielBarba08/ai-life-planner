import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { useTheme } from '../theme/ThemeContext';
import { type } from '../theme/tokens';

/**
 * Anillo de progreso circular (pedido por Daniel a partir del mockup de
 * referencia: los anillos "68%"/"60%" de la pantalla de Objetivos). Solo se
 * usa donde el porcentaje viene de un dato real — en Hábitos
 * (confirmed_this_week / target_frequency_per_week, ver HabitosScreen.tsx),
 * nunca en Objetivos/Goal, que no trae ningún campo de progreso en el
 * backend: inventar un porcentaje ahí rompería el mismo principio de "nunca
 * inventar" que ya sigue el extractor de horarios (ver
 * backend/app/assistant/schedule_extractor.py).
 */
export function ProgressRing({
  pct,
  size = 56,
  strokeWidth = 6,
  label,
}: {
  /** 0..1 */
  pct: number;
  size?: number;
  strokeWidth?: number;
  /** Texto chico al centro — por defecto el porcentaje redondeado. */
  label?: string;
}) {
  const { color } = useTheme();
  const clamped = Math.max(0, Math.min(1, pct));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        wrap: { width: size, height: size, alignItems: 'center', justifyContent: 'center' },
        svg: { position: 'absolute' },
        label: { ...type.caption, color: color.ink, fontSize: size < 48 ? 10 : 12 },
      }),
    [color, size]
  );

  return (
    <View style={styles.wrap}>
      <Svg width={size} height={size} style={styles.svg}>
        <Circle cx={center} cy={center} r={radius} stroke={color.surfaceAlt} strokeWidth={strokeWidth} fill="none" />
        <Circle
          cx={center}
          cy={center}
          r={radius}
          stroke={color.accent}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={`${circumference}, ${circumference}`}
          strokeDashoffset={circumference * (1 - clamped)}
          // El anillo arranca arriba (12 en punto) en vez del default de
          // SVG (3 en punto) — mismo look que el mockup de referencia.
          rotation={-90}
          origin={`${center}, ${center}`}
        />
      </Svg>
      <Text style={styles.label}>{label ?? `${Math.round(clamped * 100)}%`}</Text>
    </View>
  );
}
