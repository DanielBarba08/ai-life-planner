import React, { useEffect, useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { tasksApi } from '../api/endpoints';
import type { ConcentrationLevel, Priority, Task, TaskStatus } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { combineDateTime, splitDateTime } from '../utils/date';
import { Button } from './Button';
import { Pill } from './Pill';
import { TextField } from './TextField';

const PRIORITIES: Priority[] = ['baja', 'media', 'alta'];
const CONCENTRATION: ConcentrationLevel[] = ['baja', 'media', 'alta'];
const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'pendiente', label: 'Pendiente' },
  { value: 'completada', label: 'Completada' },
  { value: 'pospuesta', label: 'Pospuesta' },
];

/**
 * Formulario completo de tarea (crear y editar) para la pantalla de
 * gestión "Tareas" (Ajustes → Tareas) — a diferencia de QuickAddTaskModal
 * (alcance deliberadamente chico para el flujo rápido de "Mi día"), este
 * cubre todos los campos que ya soporta el backend: fecha límite,
 * dependencia de otra tarea, y estado.
 */
export function TaskFormModal({
  visible,
  onClose,
  onSaved,
  task,
  otherTasks,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
  task: Task | null;
  otherTasks: Task[];
}) {
  const { color, elevation } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        backdrop: { flex: 1, backgroundColor: 'rgba(20,20,16,0.4)', justifyContent: 'flex-end' },
        sheet: {
          backgroundColor: color.surface,
          borderTopLeftRadius: radius.xl,
          borderTopRightRadius: radius.xl,
          padding: spacing.lg,
          maxHeight: '90%',
          ...elevation.raised,
        },
        handle: { alignSelf: 'center', width: 36, height: 4, borderRadius: 2, backgroundColor: color.line, marginBottom: spacing.md },
        title: { ...type.h1, color: color.ink, marginBottom: spacing.md },
        fieldLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase', marginBottom: spacing.sm },
        choiceRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
        pillWrap: { marginRight: spacing.sm, marginBottom: spacing.sm },
        rangeRow: { flexDirection: 'row' },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm, paddingTop: spacing.sm, borderTopWidth: 1, borderTopColor: color.line },
      }),
    [color, elevation]
  );
  const isEdit = !!task;
  const [title, setTitle] = useState('');
  const [duration, setDuration] = useState('60');
  const [priority, setPriority] = useState<Priority>('media');
  const [concentration, setConcentration] = useState<ConcentrationLevel>('media');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState<TaskStatus>('pendiente');
  const [deadlineDate, setDeadlineDate] = useState('');
  const [deadlineTime, setDeadlineTime] = useState('');
  const [dependsOnId, setDependsOnId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) return;
    if (task) {
      setTitle(task.title);
      setDuration(String(task.duration_est_min));
      setPriority(task.priority);
      setConcentration(task.concentration_level);
      setCategory(task.category || '');
      setStatus(task.status);
      if (task.deadline) {
        const { date, time } = splitDateTime(task.deadline);
        setDeadlineDate(date);
        setDeadlineTime(time);
      } else {
        setDeadlineDate('');
        setDeadlineTime('');
      }
      setDependsOnId(task.depends_on_id);
    } else {
      setTitle('');
      setDuration('60');
      setPriority('media');
      setConcentration('media');
      setCategory('');
      setStatus('pendiente');
      setDeadlineDate('');
      setDeadlineTime('');
      setDependsOnId(null);
    }
    setError(null);
  }, [visible, task]);

  const submit = async () => {
    const minutes = parseInt(duration, 10);
    if (!title.trim() || !minutes || minutes <= 0) {
      setError('Falta un título o una duración válida.');
      return;
    }
    if ((deadlineDate && !deadlineTime) || (!deadlineDate && deadlineTime)) {
      setError('La fecha límite necesita fecha y hora, o ninguna de las dos.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const body = {
        title: title.trim(),
        duration_est_min: minutes,
        priority,
        concentration_level: concentration,
        category: category.trim() || null,
        deadline: deadlineDate && deadlineTime ? combineDateTime(deadlineDate, deadlineTime) : null,
        depends_on_id: dependsOnId,
      };
      if (isEdit && task) {
        await tasksApi.update(task.id, { ...body, status });
      } else {
        await tasksApi.create(body);
      }
      onSaved();
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={styles.title}>{isEdit ? 'Editar tarea' : 'Nueva tarea'}</Text>

            <TextField label="Título" value={title} onChangeText={setTitle} placeholder="Terminar reporte de ventas" />
            <TextField label="Duración estimada (min)" value={duration} onChangeText={setDuration} keyboardType="numeric" placeholder="60" />
            <TextField label="Categoría (opcional)" value={category} onChangeText={setCategory} placeholder="estudio, entrenamiento…" />

            <Text style={styles.fieldLabel}>Prioridad</Text>
            <ChoiceRow options={PRIORITIES} value={priority} onChange={setPriority} />

            <Text style={styles.fieldLabel}>Concentración requerida</Text>
            <ChoiceRow options={CONCENTRATION} value={concentration} onChange={setConcentration} />

            {isEdit ? (
              <>
                <Text style={styles.fieldLabel}>Estado</Text>
                <View style={styles.choiceRow}>
                  {STATUSES.map((opt) => (
                    <Pressable key={opt.value} onPress={() => setStatus(opt.value)} style={styles.pillWrap}>
                      <Pill
                        label={opt.label}
                        fg={opt.value === status ? color.accentInk : color.muted}
                        bg={opt.value === status ? color.accent : color.surfaceAlt}
                      />
                    </Pressable>
                  ))}
                </View>
              </>
            ) : null}

            <Text style={styles.fieldLabel}>Fecha límite (opcional)</Text>
            <View style={styles.rangeRow}>
              <View style={{ flex: 1 }}>
                <TextField label="Fecha" value={deadlineDate} onChangeText={setDeadlineDate} placeholder="2026-09-20" />
              </View>
              <View style={{ width: spacing.sm }} />
              <View style={{ flex: 1 }}>
                <TextField label="Hora" value={deadlineTime} onChangeText={setDeadlineTime} placeholder="18:00" />
              </View>
            </View>

            {otherTasks.length > 0 ? (
              <>
                <Text style={styles.fieldLabel}>Depende de (opcional)</Text>
                <View style={styles.choiceRow}>
                  <Pressable onPress={() => setDependsOnId(null)} style={styles.pillWrap}>
                    <Pill label="Ninguna" fg={dependsOnId === null ? color.accentInk : color.muted} bg={dependsOnId === null ? color.accent : color.surfaceAlt} />
                  </Pressable>
                  {otherTasks.map((t) => (
                    <Pressable key={t.id} onPress={() => setDependsOnId(t.id)} style={styles.pillWrap}>
                      <Pill
                        label={t.title.length > 20 ? `${t.title.slice(0, 20)}…` : t.title}
                        fg={dependsOnId === t.id ? color.accentInk : color.muted}
                        bg={dependsOnId === t.id ? color.accent : color.surfaceAlt}
                      />
                    </Pressable>
                  ))}
                </View>
              </>
            ) : null}

            {error ? <Text style={styles.error}>{error}</Text> : null}
          </ScrollView>

          <View style={styles.actions}>
            <Button label="Cancelar" variant="ghost" onPress={onClose} />
            <View style={{ width: spacing.sm }} />
            <Button label={isEdit ? 'Guardar' : 'Agregar'} onPress={submit} loading={loading} />
          </View>
        </View>
      </View>
    </Modal>
  );
}

function ChoiceRow<T extends string>({ options, value, onChange }: { options: T[]; value: T; onChange: (v: T) => void }) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        choiceRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
        pillWrap: { marginRight: spacing.sm, marginBottom: spacing.sm },
      }),
    []
  );
  return (
    <View style={styles.choiceRow}>
      {options.map((opt) => (
        <Pressable key={opt} onPress={() => onChange(opt)} style={styles.pillWrap}>
          <Pill label={opt} fg={opt === value ? color.accentInk : color.muted} bg={opt === value ? color.accent : color.surfaceAlt} />
        </Pressable>
      ))}
    </View>
  );
}
