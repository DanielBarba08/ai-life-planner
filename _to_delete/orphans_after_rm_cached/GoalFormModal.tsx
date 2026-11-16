import React, { useEffect, useMemo, useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { goalsApi } from '../api/endpoints';
import type { Goal, GoalHorizon, GoalStatus } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { Button } from './Button';
import { Pill } from './Pill';
import { TextField } from './TextField';

const HORIZONS: { value: GoalHorizon; label: string }[] = [
  { value: 'hoy', label: 'Hoy' },
  { value: 'semana', label: 'Esta semana' },
  { value: 'mes', label: 'Este mes' },
  { value: 'largo_plazo', label: 'Largo plazo' },
];

const STATUSES: { value: GoalStatus; label: string }[] = [
  { value: 'activo', label: 'Activo' },
  { value: 'completado', label: 'Completado' },
  { value: 'archivado', label: 'Archivado' },
];

export function GoalFormModal({
  visible,
  onClose,
  onSaved,
  goal,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
  goal: Goal | null;
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
          ...elevation.raised,
        },
        handle: { alignSelf: 'center', width: 36, height: 4, borderRadius: 2, backgroundColor: color.line, marginBottom: spacing.md },
        title: { ...type.h1, color: color.ink, marginBottom: spacing.md },
        fieldLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase', marginBottom: spacing.sm },
        choiceRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
        pillWrap: { marginRight: spacing.sm, marginBottom: spacing.sm },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm },
      }),
    [color, elevation]
  );
  const isEdit = !!goal;
  const [title, setTitle] = useState('');
  const [horizon, setHorizon] = useState<GoalHorizon>('semana');
  const [status, setStatus] = useState<GoalStatus>('activo');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) return;
    if (goal) {
      setTitle(goal.title);
      setHorizon(goal.horizon);
      setStatus(goal.status);
    } else {
      setTitle('');
      setHorizon('semana');
      setStatus('activo');
    }
    setError(null);
  }, [visible, goal]);

  const submit = async () => {
    if (!title.trim()) {
      setError('Falta un título.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      if (isEdit && goal) {
        await goalsApi.update(goal.id, { title: title.trim(), horizon, status });
      } else {
        await goalsApi.create({ title: title.trim(), horizon });
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
          <Text style={styles.title}>{isEdit ? 'Editar objetivo' : 'Nuevo objetivo'}</Text>

          <TextField label="Título" value={title} onChangeText={setTitle} placeholder="Entrenar tres veces esta semana" />

          <Text style={styles.fieldLabel}>Horizonte</Text>
          <View style={styles.choiceRow}>
            {HORIZONS.map((h) => (
              <Pressable key={h.value} onPress={() => setHorizon(h.value)} style={styles.pillWrap}>
                <Pill label={h.label} fg={horizon === h.value ? color.accentInk : color.muted} bg={horizon === h.value ? color.accent : color.surfaceAlt} />
              </Pressable>
            ))}
          </View>

          {isEdit ? (
            <>
              <Text style={styles.fieldLabel}>Estado</Text>
              <View style={styles.choiceRow}>
                {STATUSES.map((s) => (
                  <Pressable key={s.value} onPress={() => setStatus(s.value)} style={styles.pillWrap}>
                    <Pill label={s.label} fg={status === s.value ? color.accentInk : color.muted} bg={status === s.value ? color.accent : color.surfaceAlt} />
                  </Pressable>
                ))}
              </View>
            </>
          ) : null}

          {error ? <Text style={styles.error}>{error}</Text> : null}

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
