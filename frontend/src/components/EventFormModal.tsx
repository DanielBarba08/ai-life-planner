import React, { useEffect, useMemo, useState } from 'react';
import { Modal, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../api/client';
import { eventsApi } from '../api/endpoints';
import type { FixedEvent } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { combineDateTime, splitDateTime } from '../utils/date';
import { Button } from './Button';
import { TextField } from './TextField';

/** Crear/editar un evento fijo — el Planning Engine nunca los reprograma
 * solo (son inamovibles por diseño, ver backend/README.md), así que esta
 * es la única forma de corregir uno si cambia de horario. */
export function EventFormModal({
  visible,
  onClose,
  onSaved,
  event,
}: {
  visible: boolean;
  onClose: () => void;
  onSaved: () => void;
  event: FixedEvent | null;
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
        rangeRow: { flexDirection: 'row' },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        actions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm },
      }),
    [color, elevation]
  );
  const isEdit = !!event;
  const [title, setTitle] = useState('');
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!visible) return;
    if (event) {
      setTitle(event.title);
      const s = splitDateTime(event.start);
      const e = splitDateTime(event.end);
      setStartDate(s.date);
      setStartTime(s.time);
      setEndDate(e.date);
      setEndTime(e.time);
    } else {
      setTitle('');
      setStartDate('');
      setStartTime('');
      setEndDate('');
      setEndTime('');
    }
    setError(null);
  }, [visible, event]);

  const submit = async () => {
    if (!title.trim() || !startDate || !startTime || !endDate || !endTime) {
      setError('Completa título, inicio y fin.');
      return;
    }
    const start = combineDateTime(startDate, startTime);
    const end = combineDateTime(endDate, endTime);
    if (end <= start) {
      setError('El fin debe ser después del inicio.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      if (isEdit && event) {
        await eventsApi.update(event.id, { title: title.trim(), start, end });
      } else {
        await eventsApi.create({ title: title.trim(), start, end });
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
          <Text style={styles.title}>{isEdit ? 'Editar evento' : 'Nuevo evento'}</Text>

          <TextField label="Título" value={title} onChangeText={setTitle} placeholder="Junta de equipo" />

          <Text style={styles.fieldLabel}>Inicio</Text>
          <View style={styles.rangeRow}>
            <View style={{ flex: 1 }}>
              <TextField label="Fecha" value={startDate} onChangeText={setStartDate} placeholder="2026-09-20" />
            </View>
            <View style={{ width: spacing.sm }} />
            <View style={{ flex: 1 }}>
              <TextField label="Hora" value={startTime} onChangeText={setStartTime} placeholder="09:00" />
            </View>
          </View>

          <Text style={styles.fieldLabel}>Fin</Text>
          <View style={styles.rangeRow}>
            <View style={{ flex: 1 }}>
              <TextField label="Fecha" value={endDate} onChangeText={setEndDate} placeholder="2026-09-20" />
            </View>
            <View style={{ width: spacing.sm }} />
            <View style={{ flex: 1 }}>
              <TextField label="Hora" value={endTime} onChangeText={setEndTime} placeholder="10:00" />
            </View>
          </View>

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
