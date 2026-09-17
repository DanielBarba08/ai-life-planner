import React, { useEffect, useMemo, useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { habitsApi } from '../api/endpoints';
import type { ConcentrationLevel, Habit, HabitStatus } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { Button } from './Button';
import { Pill } from './Pill';
import { TextField } from './TextField';

const CONCENTRATION: ConcentrationLevel[] = ['baja', 'media', 'alta'];
const FREQUENCIES = [1, 2, 3, 4, 5, 6, 7];
const STATUSES: { value: HabitStatus; label: string }[] = [
  { value: 'activo', label: 'Activo' },
  { value: 'pausado', label: 'Pausado' },
];

/**
 * Crear/editar un hábito recurrente (Ajustes → Hábitos, Fase 5 del
 * roadmap). Este formulario NUNCA crea las sesiones de la semana — solo
 * describe la meta ("entrenar 3 veces por semana"); las sesiones se
 * proponen y confirman aparte, en HabitosScreen (ver
 * backend/app/habits/service.py y el punto 14 del brief: nunca crear
 * algo así sin confirmación explícita).
 */
export function HabitFormModal({
  visible,
  onClose,
  onSaved,
  habit,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
  habit: Habit | null;
}) {
  const { color, elevation } = useTheme();
  const styles = useMemo(
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
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm, paddingTop: spacing.sm, borderTopWidth: 1, borderTopColor: color.line },
      }),
    [color, elevation]
  );
  const isEdit = !!habit;
  const [title, setTitle] = useState('');
  const [frequency, setFrequency] = useState(3);
  const [duration, setDuration] = useState('45');
  const [concentration, setConcentration] = useState<ConcentrationLevel>('media');
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState<HabitStatus>('activo');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) return;
    if (habit) {
      setTitle(habit.title);
      setFrequency(habit.target_frequency_per_week);
      setDuration(String(habit.duration_est_min));
      setConcentration(habit.concentration_level);
      setCategory(habit.category || '');
      setStatus(habit.status);
    } else {
      setTitle('');
      setFrequency(3);
      setDuration('45');
      setConcentration('media');
      setCategory('');
      setStatus('activo');
    }
    setError(null);
  }, [visible, habit]);

  const submit = async () => {
    const minutes = parseInt(duration, 10);
    if (!title.trim() || !minutes || minutes <= 0) {
      setError('Falta un título o una duración válida.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const body = {
        title: title.trim(),
        target_frequency_per_week: frequency,
        duration_est_min: minutes,
        concentration_level: concentration,
        category: category.trim() || null,
      };
      if (isEdit && habit) {
        await habitsApi.update(habit.id, { ...body, status });
      } else {
        await habitsApi.create(body);
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
            <Text style={styles.title}>{isEdit ? 'Editar hábito' : 'Nuevo hábito'}</Text>

            <TextField label="Título" value={title} onChangeText={setTitle} placeholder="Entrenar" />
            <TextField label="Duración por sesión (min)" value={duration} onChangeText={setDuration} keyboardType="numeric" placeholder="45" />
            <TextField label="Categoría (opcional)" value={category} onChangeText={setCategory} placeholder="entrenamiento, estudio…" />

            <Text style={styles.fieldLabel}>Veces por semana</Text>
            <View style={styles.choiceRow}>
              {FREQUENCIES.map((n) => (
                <Pressable key={n} onPress={() => setFrequency(n)} style={styles.pillWrap}>
                  <Pill label={String(n)} fg={n === frequency ? color.accentInk : color.muted} bg={n === frequency ? color.accent : color.surfaceAlt} />
                </Pressable>
              ))}
            </View>

            <Text style={styles.fieldLabel}>Concentración requerida</Text>
            <View style={styles.choiceRow}>
              {CONCENTRATION.map((c) => (
                <Pressable key={c} onPress={() => setConcentration(c)} style={styles.pillWrap}>
                  <Pill label={c} fg={c === concentration ? color.accentInk : color.muted} bg={c === concentration ? color.accent : color.surfaceAlt} />
                </Pressable>
              ))}
            </View>

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
