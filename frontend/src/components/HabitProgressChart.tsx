import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { HabitProgressWeek } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { dayOfMonth } from '../utils/date';

const TRACK_HEIGHT = 64;

/**
 * Barras de progreso semanal de un hábito (pedido por Daniel el 12 nov:
 * "con gráficas mostrar el progreso en las semanas") — GET
 * /v1/habits/{id}/progress, ver HabitosScreen.tsx.
 *
 * La barra mide `completed / target_frequency_per_week` de esa semana,
 * no `confirmed`: desde que las sesiones se auto-confirman solas cada
 * semana (ver app/habits/service.py::auto_confirm_due_sessions),
 * "confirmed" prácticamente siempre toca el objetivo — ya no distingue
 * nada. Lo que de verdad varía semana a semana, y lo que a Daniel le
 * interesa ver, es cuántas de esas sesiones programadas se completaron
 * de verdad.
 */
export function HabitProgressChart({ weeks }: { weeks: HabitProgressWeek[] }) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        row: { flexDirection: 'row', alignItems: 'flex-end' },
        col: { flex: 1, alignItems: 'center' },
        count: { ...type.caption, color: color.ink, fontSize: 11, marginBottom: 2 },
        track: {
          width: '100%',
          maxWidth: 22,
          height: TRACK_HEIGHT,
          borderRadius: radius.sm,
          backgroundColor: color.surfaceAlt,
          overflow: 'hidden',
          justifyContent: 'flex-end',
        },
        fill: { width: '100%', backgroundColor: color.accent },
        label: { ...type.caption, color: color.muted, marginTop: spacing.xs, fontSize: 10 },
      }),
    [color]
  );

  return (
    <View style={styles.row}>
      {weeks.map((w) => {
        const target = w.target_frequency_per_week || 1;
        const pct = Math.min(1, w.completed / target);
        return (
          <View key={w.week_start} style={styles.col}>
            <Text style={styles.count}>{w.completed}</Text>
            <View style={styles.track}>
              <View style={[styles.fill, { height: `${Math.round(pct * 100)}%` }]} />
            </View>
            <Text style={styles.label}>{dayOfMonth(w.week_start)}</Text>
          </View>
        );
      })}
    </View>
  );
}
