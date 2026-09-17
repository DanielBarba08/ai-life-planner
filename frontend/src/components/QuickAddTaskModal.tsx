import React, { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { tasksApi } from '../api/endpoints';
import type { ConcentrationLevel, Priority } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { Button } from './Button';
import { Pill } from './Pill';
import { TextField } from './TextField';

const PRIORITIES: Priority[] = ['baja', 'media', 'alta'];
const CONCENTRATION: ConcentrationLevel[] = ['baja', 'media', 'alta'];

/**
 * Alcance deliberadamente chico: título, duración, prioridad, nivel de
 * concentración y categoría libre — los mismos campos que ya prueba el
 * backend (tests/test_tasks.py). Fecha límite y dependencias entre tareas
 * quedan para una pantalla de "editar tarea" completa más adelante; esto
 * es lo mínimo para poder ver el Planning Engine funcionando de verdad
 * desde la app, no un CRUD completo de tareas todavía.
 */
export function QuickAddTaskModal({ visible, onClose, onCreated }: { visible: boolean; onClose: () => void; onCreated: () => void }) {
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
          ...elevation.raised,
        },
        handle: { alignSelf: 'center', width: 36, height: 4, borderRadius: 2, backgroundColor: color.line, marginBottom: spacing.md },
        title: { ...type.h1, color: color.ink, marginBottom: spacing.md },
        fieldLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase', marginBottom: spacing.sm },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm },
      }),
    [color, elevation]
  );
  const [title, setTitle] = useState('');
  const [duration, setDuration] = useState('60');
  const [priority, setPriority] = useState<Priority>('media');
  const [concentration, setConcentration] = useState<ConcentrationLevel>('media');
  const [category, setCategory] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const reset = () => {
    setTitle('');
    setDuration('60');
    setPriority('media');
    setConcentration('media');
    setCategory('');
    setError(null);
  };

  const submit = async () => {
    const minutes = parseInt(duration, 10);
    if (!title.trim() || !minutes || minutes <= 0) {
      setError('Falta un título o una duración válida.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await tasksApi.create({
        title: title.trim(),
        duration_est_min: minutes,
        priority,
        concentration_level: concentration,
        category: category.trim() || null,
      });
      reset();
      onCreated();
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
          <Text style={styles.title}>Nueva tarea</Text>

          <TextField label="Título" value={title} onChangeText={setTitle} placeholder="Terminar reporte de ventas" />
          <TextField label="Duración estimada (min)" value={duration} onChangeText={setDuration} keyboardType="numeric" placeholder="60" />
          <TextField label="Categoría (opcional)" value={category} onChangeText={setCategory} placeholder="estudio, entrenamiento…" />

          <Text style={styles.fieldLabel}>Prioridad</Text>
          <ChoiceRow options={PRIORITIES} value={priority} onChange={setPriority} />

          <Text style={styles.fieldLabel}>Concentración requerida</Text>
          <ChoiceRow options={CONCENTRATION} value={concentration} onChange={setConcentration} />

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <View style={styles.actions}>
            <Button label="Cancelar" variant="ghost" onPress={onClose} />
            <View style={{ width: spacing.sm }} />
            <Button label="Agregar" onPress={submit} loading={loading} />
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
      }),
    []
  );
  return (
    <View style={styles.choiceRow}>
      {options.map((opt) => (
        <Pressable key={opt} onPress={() => onChange(opt)} style={{ marginRight: spacing.sm, marginBottom: spacing.sm }}>
          <Pill label={opt} fg={opt === value ? color.accentInk : color.muted} bg={opt === value ? color.accent : color.surfaceAlt} />
        </Pressable>
      ))}
    </View>
  );
}
