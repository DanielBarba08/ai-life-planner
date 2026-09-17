import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { tasksApi } from '../../api/endpoints';
import type { Task, TaskStatus } from '../../api/types';
import { BackHeader } from '../../components/BackHeader';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Pill } from '../../components/Pill';
import { Screen } from '../../components/Screen';
import { TaskFormModal } from '../../components/TaskFormModal';
import { useTheme } from '../../theme/ThemeContext';
import { spacing, type } from '../../theme/tokens';
import { wallClockTime } from '../../utils/date';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'Tareas'>;

const FILTERS: { value: TaskStatus | 'todas'; label: string }[] = [
  { value: 'todas', label: 'Todas' },
  { value: 'pendiente', label: 'Pendientes' },
  { value: 'completada', label: 'Completadas' },
  { value: 'pospuesta', label: 'Pospuestas' },
];

export default function TareasScreen({ navigation }: Props) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<TaskStatus | 'todas'>('todas');
  const [formVisible, setFormVisible] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  const statusColor: Record<TaskStatus, { fg: string; bg: string }> = React.useMemo(
    () => ({
      pendiente: { fg: color.accent, bg: color.accentSoft },
      completada: { fg: color.good, bg: color.goodSoft },
      pospuesta: { fg: color.warn, bg: color.warnSoft },
    }),
    [color]
  );

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        filterRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
        filterPillWrap: { marginRight: spacing.sm, marginBottom: spacing.sm },
        muted: { ...type.body, color: color.muted },
        taskCard: { marginBottom: spacing.sm },
        taskHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.xs },
        taskTitle: { ...type.bodyStrong, color: color.ink, flex: 1, marginRight: spacing.sm },
        taskMetaRow: { flexDirection: 'row', alignItems: 'center' },
        taskMeta: { ...type.caption, color: color.muted, marginLeft: spacing.sm },
        taskDeadline: { ...type.caption, color: color.muted, marginTop: spacing.xs },
      }),
    [color]
  );

  const tasksQuery = useQuery<Task[]>({
    queryKey: ['tasks', filter],
    queryFn: () => tasksApi.list(filter === 'todas' ? undefined : { status: filter }),
  });

  const allTasksQuery = useQuery<Task[]>({ queryKey: ['tasks', 'todas'], queryFn: () => tasksApi.list() });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
    setFormVisible(false);
    setEditingTask(null);
  };

  const remove = async (id: string) => {
    await tasksApi.remove(id);
    queryClient.invalidateQueries({ queryKey: ['tasks'] });
  };

  return (
    <Screen>
      <BackHeader title="Tareas" onBack={() => navigation.goBack()} />

      <View style={styles.filterRow}>
        {FILTERS.map((f) => (
          <Pressable key={f.value} onPress={() => setFilter(f.value)} style={styles.filterPillWrap}>
            <Pill
              label={f.label}
              fg={filter === f.value ? color.accentInk : color.muted}
              bg={filter === f.value ? color.accent : color.surfaceAlt}
            />
          </Pressable>
        ))}
      </View>

      <Button
        label="+ Nueva tarea"
        variant="secondary"
        onPress={() => {
          setEditingTask(null);
          setFormVisible(true);
        }}
      />

      <View style={{ height: spacing.md }} />

      {tasksQuery.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (tasksQuery.data ?? []).length === 0 ? (
        <Card>
          <Text style={styles.muted}>No hay tareas {filter !== 'todas' ? `en "${FILTERS.find((f) => f.value === filter)?.label.toLowerCase()}"` : 'todavía'}.</Text>
        </Card>
      ) : (
        (tasksQuery.data ?? []).map((t) => (
          <Card key={t.id} style={styles.taskCard}>
            <Pressable
              onPress={() => {
                setEditingTask(t);
                setFormVisible(true);
              }}
            >
              <View style={styles.taskHeader}>
                <Text style={styles.taskTitle} numberOfLines={1}>
                  {t.title}
                </Text>
                <Pressable onPress={() => remove(t.id)} hitSlop={8}>
                  <Ionicons name="trash-outline" size={17} color={color.muted} />
                </Pressable>
              </View>
              <View style={styles.taskMetaRow}>
                <Pill label={t.status} fg={statusColor[t.status].fg} bg={statusColor[t.status].bg} />
                <Text style={styles.taskMeta}>{t.duration_est_min} min · prioridad {t.priority}</Text>
              </View>
              {t.deadline ? (
                <Text style={styles.taskDeadline}>
                  Vence {t.deadline.slice(0, 10)} {wallClockTime(t.deadline)}
                </Text>
              ) : null}
            </Pressable>
          </Card>
        ))
      )}

      <TaskFormModal
        visible={formVisible}
        onClose={() => {
          setFormVisible(false);
          setEditingTask(null);
        }}
        onSaved={refresh}
        task={editingTask}
        otherTasks={(allTasksQuery.data ?? []).filter((t) => t.id !== editingTask?.id)}
      />
    </Screen>
  );
}
