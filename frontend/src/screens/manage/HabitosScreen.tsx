import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { habitsApi } from '../../api/endpoints';
import type { Habit, HabitProgress, HabitWeek } from '../../api/types';
import { BackHeader } from '../../components/BackHeader';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { HabitFormModal } from '../../components/HabitFormModal';
import { HabitProgressChart } from '../../components/HabitProgressChart';
import { ProgressRing } from '../../components/ProgressRing';
import { Screen } from '../../components/Screen';
import { useTheme } from '../../theme/ThemeContext';
import { radius, spacing, type } from '../../theme/tokens';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'Habitos'>;

export default function HabitosScreen({ navigation }: Props) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [formVisible, setFormVisible] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.lg },
        muted: { ...type.body, color: color.muted },
      }),
    [color]
  );

  const habitsQuery = useQuery<Habit[]>({ queryKey: ['habits'], queryFn: () => habitsApi.list() });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['habits'] });
    setFormVisible(false);
    setEditingHabit(null);
  };

  const remove = async (id: string) => {
    await habitsApi.remove(id);
    queryClient.invalidateQueries({ queryKey: ['habits'] });
  };

  return (
    <Screen>
      <BackHeader title="Hábitos" onBack={() => navigation.goBack()} />
      <Text style={styles.subtitle}>
        Metas recurrentes ("entrenar 3 veces por semana"). Cada semana se agregan solas a tu calendario según la
        frecuencia que elijas — el progreso es real, cuenta tareas de verdad, nunca un número inventado.
      </Text>

      <Button
        label="+ Nuevo hábito"
        variant="secondary"
        onPress={() => {
          setEditingHabit(null);
          setFormVisible(true);
        }}
      />
      <View style={{ height: spacing.md }} />

      {habitsQuery.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (habitsQuery.data ?? []).length === 0 ? (
        <Card>
          <Text style={styles.muted}>No tienes hábitos todavía.</Text>
        </Card>
      ) : (
        (habitsQuery.data ?? []).map((h) => (
          <HabitCard
            key={h.id}
            habit={h}
            onEdit={() => {
              setEditingHabit(h);
              setFormVisible(true);
            }}
            onDelete={() => remove(h.id)}
          />
        ))
      )}

      <HabitFormModal visible={formVisible} onClose={() => { setFormVisible(false); setEditingHabit(null); }} onSaved={refresh} habit={editingHabit} />
    </Screen>
  );
}

function HabitCard({ habit, onEdit, onDelete }: { habit: Habit; onEdit: () => void; onDelete: () => void }) {
  const { color } = useTheme();

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        card: { marginBottom: spacing.sm },
        row: { flexDirection: 'row', alignItems: 'center' },
        iconCircle: {
          width: 30,
          height: 30,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        habitTitle: { ...type.bodyStrong, color: color.ink },
        meta: { ...type.caption, color: color.muted, marginTop: 2 },
        progressBlock: { marginTop: spacing.md },
        progressTrack: { height: 8, borderRadius: radius.pill, backgroundColor: color.surfaceAlt, overflow: 'hidden' },
        progressFill: { height: '100%', borderRadius: radius.pill, backgroundColor: color.accent },
        progressLabel: { ...type.caption, color: color.muted, marginTop: spacing.xs },
        overflowNote: { ...type.caption, color: color.muted, marginTop: spacing.xs, fontStyle: 'italic' },
        chartBlock: { marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: color.line },
        chartTitle: { ...type.caption, color: color.muted, marginBottom: spacing.sm },
      }),
    [color]
  );

  const weekQuery = useQuery<HabitWeek>({
    queryKey: ['habit-week', habit.id],
    queryFn: () => habitsApi.week(habit.id),
  });
  const progressQuery = useQuery<HabitProgress>({
    queryKey: ['habit-progress', habit.id],
    queryFn: () => habitsApi.progress(habit.id, 6),
  });

  const week = weekQuery.data;
  const target = week?.target_frequency_per_week ?? habit.target_frequency_per_week;
  const confirmed = week?.confirmed_this_week ?? 0;
  const completed = week?.completed_this_week ?? 0;
  const pct = target > 0 ? Math.min(1, confirmed / target) : 0;

  return (
    <Card style={styles.card}>
      <Pressable onPress={onEdit}>
        <View style={styles.row}>
          <View style={styles.iconCircle}>
            <Ionicons name="sync" size={14} color={color.accent} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.habitTitle}>{habit.title}</Text>
            <Text style={styles.meta}>
              {habit.duration_est_min} min · {habit.concentration_level}
              {habit.status === 'pausado' ? ' · pausado' : ''}
            </Text>
          </View>
          <ProgressRing pct={pct} size={44} strokeWidth={5} />
          <Pressable onPress={onDelete} hitSlop={8} style={{ marginLeft: spacing.sm }}>
            <Ionicons name="trash-outline" size={17} color={color.muted} />
          </Pressable>
        </View>
      </Pressable>

      <View style={styles.progressBlock}>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${Math.round(pct * 100)}%` }]} />
        </View>
        <Text style={styles.progressLabel}>
          {confirmed} de {target} esta semana ya en tu calendario
          {completed > 0 ? ` · ${completed} completada${completed === 1 ? '' : 's'}` : ''}
        </Text>
        {/* Caso borde: una meta más alta que los días que quedan en la
            semana (ej. 14x/semana creado un jueves) nunca se alcanza del
            todo en una sola semana — se avisa en vez de mostrar un botón
            que no haría nada, porque ya no queda ningún día libre que
            confirmar (ver habits_service.auto_confirm_due_sessions). */}
        {week && week.remaining_to_suggest > 0 ? (
          <Text style={styles.overflowNote}>
            Tu meta es más alta que los días que quedan esta semana — seguimos la próxima.
          </Text>
        ) : null}
      </View>

      {progressQuery.data && progressQuery.data.weeks.length > 0 ? (
        <View style={styles.chartBlock}>
          <Text style={styles.chartTitle}>Progreso de las últimas semanas</Text>
          <HabitProgressChart weeks={progressQuery.data.weeks} />
        </View>
      ) : null}
    </Card>
  );
}
