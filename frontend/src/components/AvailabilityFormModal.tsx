import React, { useEffect, useMemo, useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { availabilityApi } from '../api/endpoints';
import type { AvailabilityType } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type as txt } from '../theme/tokens';
import { Button } from './Button';
import { Pill } from './Pill';
import { TextField } from './TextField';

const TYPES: { value: AvailabilityType; label: string }[] = [
  { value: 'trabajo', label: 'Trabajo' },
  { value: 'escuela', label: 'Escuela' },
  { value: 'personal', label: 'Personal' },
  { value: 'otro', label: 'Otro' },
];

const DAYS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];

/** Solo crear/borrar — el backend no tiene PATCH para disponibilidad
 * (ver app/routers/availability.py), así que "editar" un bloque es
 * borrarlo y crear uno nuevo con los datos corregidos. */
export function AvailabilityFormModal({ visible, onClose, onSaved }: { visible: boolean; onClose: () => void; onSaved: () => void }) {
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
        title: { ...txt.h1, color: color.ink, marginBottom: spacing.md },
        fieldLabel: { ...txt.caption, color: color.muted, textTransform: 'uppercase', marginBottom: spacing.sm },
        choiceRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md },
        pillWrap: { marginRight: spacing.sm, marginBottom: spacing.sm },
        rangeRow: { flexDirection: 'row' },
        error: { color: color.danger, ...txt.body, marginTop: spacing.md, marginBottom: spacing.sm },
        actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.md },
      }),
    [color, elevation]
  );
  const [type, setType] = useState<AvailabilityType>('trabajo');
  const [dayOfWeek, setDayOfWeek] = useState(0);
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) return;
    setType('trabajo');
    setDayOfWeek(0);
    setStart('');
    setEnd('');
    setError(null);
  }, [visible]);

  const submit = async () => {
    if (!start || !end) {
      setError('Completa desde y hasta.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await availabilityApi.create({ type, day_of_week: dayOfWeek, start: `${start}:00`, end: `${end}:00` });
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
          <Text style={styles.title}>Nuevo bloque recurrente</Text>

          <Text style={styles.fieldLabel}>Tipo</Text>
          <View style={styles.choiceRow}>
            {TYPES.map((t) => (
              <Pressable key={t.value} onPress={() => setType(t.value)} style={styles.pillWrap}>
                <Pill label={t.label} fg={type === t.value ? color.accentInk : color.muted} bg={type === t.value ? color.accent : color.surfaceAlt} />
              </Pressable>
            ))}
          </View>

          <Text style={styles.fieldLabel}>Día</Text>
          <View style={styles.choiceRow}>
            {DAYS.map((d, i) => (
              <Pressable key={d} onPress={() => setDayOfWeek(i)} style={styles.pillWrap}>
                <Pill label={d} fg={dayOfWeek === i ? color.accentInk : color.muted} bg={dayOfWeek === i ? color.accent : color.surfaceAlt} />
              </Pressable>
            ))}
          </View>

          <View style={styles.rangeRow}>
            <View style={{ flex: 1 }}>
              <TextField label="Desde" value={start} onChangeText={setStart} placeholder="09:00" />
            </View>
            <View style={{ width: spacing.sm }} />
            <View style={{ flex: 1 }}>
              <TextField label="Hasta" value={end} onChangeText={setEnd} placeholder="17:00" />
            </View>
          </View>

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
