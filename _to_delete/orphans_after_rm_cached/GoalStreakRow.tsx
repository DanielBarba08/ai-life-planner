import { Ionicons } from '@expo/vector-icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { goalsApi } from '../api/endpoints';
import type { Goal, GoalStreak } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';

/**
 * "¿Cumpliste tu objetivo hoy?" + racha — pedido por Daniel el 8 nov:
 * preguntar día con día si se cumplió cada objetivo, hacer crecer una
 * racha real a partir de esas respuestas (GoalCheckin/GoalStreakRead en
 * el backend, mismo patrón que la racha de "Mi día") y mostrarla para
 * motivar al usuario.
 *
 * Es un componente propio (no vive solo en ObjetivosScreen) porque se usa
 * en dos lugares: ahí, donde se gestionan los objetivos a detalle, y en
 * el widget de Mi día — para que contestar la pregunta del día no
 * obligue a salir de la pantalla principal.
 *
 * Solo pinta algo para objetivos activos: un objetivo completado o
 * archivado ya no tiene sentido seguir "confirmando" día con día.
 */
export function GoalStreakRow({ goal }: { goal: Goal }) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [sending, setSending] = useState(false);

  const streakQuery = useQuery<GoalStreak>({
    queryKey: ['goal-streak', goal.id],
    queryFn: () => goalsApi.streak(goal.id),
    enabled: goal.status === 'activo',
  });

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        wrap: { marginTop: spacing.sm, paddingTop: spacing.sm, borderTopWidth: 1, borderTopColor: color.line },
        row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
        pill: {
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: color.streakSoft,
          borderRadius: radius.pill,
          paddingVertical: 4,
          paddingHorizontal: spacing.sm,
        },
        pillMuted: { backgroundColor: color.surfaceAlt },
        pillText: { ...type.caption, color: color.streak, marginLeft: spacing.xs },
        pillTextMuted: { color: color.muted },
        confirmedRow: { flexDirection: 'row', alignItems: 'center' },
        confirmedText: { ...type.caption, color: color.muted, marginLeft: spacing.xs },
        askRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.sm },
        question: { ...type.caption, color: color.muted, flex: 1, marginRight: spacing.sm },
        chipsRow: { flexDirection: 'row' },
        chip: { paddingVertical: 6, paddingHorizontal: spacing.sm, borderRadius: radius.pill, marginLeft: spacing.xs },
        chipNo: { backgroundColor: color.surfaceAlt },
        chipYes: { backgroundColor: color.goodSoft },
        chipText: { ...type.caption },
      }),
    [color]
  );

  if (goal.status !== 'activo' || streakQuery.isLoading) return null;

  const streak = streakQuery.data;
  if (!streak) return null;

  const checkin = async (completed: boolean) => {
    setSending(true);
    try {
      const updated = await goalsApi.checkin(goal.id, completed);
      queryClient.setQueryData(['goal-streak', goal.id], updated);
    } finally {
      setSending(false);
    }
  };

  const showStreak = streak.current_streak > 0;

  return (
    <View style={styles.wrap}>
      <View style={styles.row}>
        <View style={[styles.pill, !showStreak && styles.pillMuted]}>
          <Ionicons name={showStreak ? 'flame' : 'flame-outline'} size={13} color={showStreak ? color.streak : color.muted} />
          <Text style={[styles.pillText, !showStreak && styles.pillTextMuted]}>
            {showStreak ? `${streak.current_streak} ${streak.current_streak === 1 ? 'día seguido' : 'días seguidos'}` : 'Sin racha todavía'}
          </Text>
        </View>

        {streak.checked_in_today ? (
          <View style={styles.confirmedRow}>
            <Ionicons
              name={streak.completed_today ? 'checkmark-circle' : 'close-circle'}
              size={15}
              color={streak.completed_today ? color.good : color.muted}
            />
            <Text style={styles.confirmedText}>{streak.completed_today ? 'Hoy cumplido' : 'Hoy no cumplido'}</Text>
          </View>
        ) : null}
      </View>

      {!streak.checked_in_today ? (
        <View style={styles.askRow}>
          <Text style={styles.question}>¿Cumpliste hoy?</Text>
          <View style={styles.chipsRow}>
            <Pressable style={[styles.chip, styles.chipNo]} onPress={() => checkin(false)} disabled={sending}>
              <Text style={[styles.chipText, { color: color.muted }]}>No</Text>
            </Pressable>
            <Pressable style={[styles.chip, styles.chipYes]} onPress={() => checkin(true)} disabled={sending}>
              <Text style={[styles.chipText, { color: color.good }]}>Sí</Text>
            </Pressable>
          </View>
        </View>
      ) : null}
    </View>
  );
}
