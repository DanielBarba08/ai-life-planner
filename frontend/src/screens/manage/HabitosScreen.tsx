import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { habitsApi } from '../../api/endpoints';
import type { Habit, HabitWeek } from '../../api/types';
import { BackHeader } from '../../components/BackHeader';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { HabitFormModal } from '../../components/HabitFormModal';
import { Screen } from '../../components/Screen';
import { useTheme } from '../../theme/ThemeContext';
import { radius, spacing, type } from '../../theme/tokens';
import { shortWeekdayLabel } from '../../utils/date';
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
        Metas recurrentes ("entrenar 3 veces por semana"). El progreso es real — cuenta tareas de verdad que tú
        confirmas cada semana, nunca se agregan solas al calendario.
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
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

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
        suggestBlock: { marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: color.line },
        suggestLabel: { ...type.caption, color: color.muted, marginBottom: spacing.sm },
      }),
    [color]
  );

  const weekQuery = useQuery<HabitWeek>({
    queryKey: ['habit-week', habit.id],
    queryFn: () => habitsApi.week(habit.id),
  });

  const confirmSuggested = async () => {
    if (!weekQuery.data || weekQuery.data.suggested_sessions.length === 0) return;
    setConfirming(true);
    try {
      await habitsApi.confirmWeek(habit.id, weekQuery.data.suggested_sessions);
      queryClient.invalidateQueries({ queryKey: ['habit-week', habit.id] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    } finally {
      setConfirming(false);
    }
  };

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
          <Pressable onPress={onDelete} hitSlop={8}>
            <Ionicons name="trash-outline" size={17} color={color.muted} />
          </Pressable>
        </View>
      </Pressable>

      <View style={styles.progressBlock}>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${Math.round(pct * 100)}%` }]} />
        </View>
        <Text style={styles.progressLabel}>
          {confirmed} de {target} esta semana{completed > 0 ? ` · ${completed} completada${completed === 1 ? '' : 's'}` : ''}
        </Text>
      </View>

      {week && week.suggested_sessions.length > 0 ? (
        <View style={styles.suggestBlock}>
          <Text style={styles.suggestLabel}>
            Faltan {week.remaining_to_suggest} sesion{week.remaining_to_suggest === 1 ? '' : 'es'} — propuestas
            para: {week.suggested_sessions.map((s) => shortWeekdayLabel(s.suggested_date)).join(', ')}
          </Text>
          <Button label="Agregar a mi semana" variant="secondary" onPress={confirmSuggested} loading={confirming} />
        </View>
      ) : null}
    </Card>
  );
}
