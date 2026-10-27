import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { assistantApi } from '../../api/endpoints';
import type { ScheduleItem } from '../../api/types';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Screen } from '../../components/Screen';
import { TextField } from '../../components/TextField';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';

interface ChatMessage {
  id: string;
  from: 'user' | 'assistant';
  text: string;
  pendingImport?: ScheduleItem[];
  importStatus?: 'pending' | 'confirmed' | 'cancelled';
}

const EXAMPLES = [
  'Organiza mi tarde',
  '¿Qué hago ahora?',
  'Optimiza mi día',
  'No terminé las tareas de ayer',
  'Importa mi horario: trabajo 9 a 6 lunes a viernes',
];

const DAY_ABBR = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];

function hhmm(value: string): string {
  return value.slice(0, 5);
}

function describeScheduleItem(item: ScheduleItem): string {
  const rango = `${hhmm(item.start)}–${hhmm(item.end)}`;
  if (item.kind === 'availability') {
    const dias = item.days.map((d) => DAY_ABBR[d]).join(', ');
    return `${item.label} · ${dias} · ${rango}`;
  }
  const [, month, day] = item.date.split('-');
  return `${item.label} · ${day}/${month} · ${rango}`;
}

export default function AsistenteScreen() {
  const { color, elevation } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        header: { padding: spacing.lg, paddingBottom: 0 },
        eyebrow: { ...type.caption, color: color.accent, textTransform: 'uppercase' },
        title: { ...type.display, color: color.ink, marginTop: spacing.xs, marginBottom: spacing.md },
        list: { padding: spacing.lg, paddingTop: spacing.sm, gap: spacing.sm },
        bubble: { maxWidth: '78%', padding: spacing.md, borderRadius: radius.lg, marginBottom: spacing.sm },
        bubbleUser: { backgroundColor: color.accent, alignSelf: 'flex-end', borderBottomRightRadius: radius.sm, ...elevation.low },
        bubbleAssistant: { backgroundColor: color.surface, borderBottomLeftRadius: radius.sm, borderWidth: 1, borderColor: color.line, flexShrink: 1 },
        bubbleUserText: { ...type.body, color: color.accentInk },
        bubbleAssistantText: { ...type.body, color: color.ink },
        assistantRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: spacing.sm, marginTop: 2 },
        assistantAvatar: {
          width: 24,
          height: 24,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.xs,
        },
        examplesRow: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: spacing.lg, gap: spacing.sm, marginBottom: spacing.sm },
        exampleChip: {
          ...type.caption,
          color: color.accent,
          backgroundColor: color.accentSoft,
          paddingHorizontal: spacing.sm,
          paddingVertical: 6,
          borderRadius: radius.pill,
          overflow: 'hidden',
        },
        inputRow: { flexDirection: 'row', alignItems: 'flex-end', padding: spacing.lg, paddingTop: 0 },
        input: { marginBottom: 0 },
        importCard: { marginLeft: 32, marginTop: -spacing.xs, marginBottom: spacing.sm, maxWidth: '82%' },
        importItem: { ...type.caption, color: color.ink, marginBottom: 4 },
        importActions: { flexDirection: 'row', marginTop: spacing.sm },
        importResolvedText: { ...type.caption, color: color.muted, fontStyle: 'italic' },
      }),
    [color, elevation]
  );
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      from: 'assistant',
      text:
        'Puedo ayudarte con tu día real — prueba "optimiza mi día", "¿qué hago ahora?", "quiero entrenar tres veces esta semana", o pégame tu horario completo con "importa mi horario: ...".',
    },
  ]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const [importingId, setImportingId] = useState<string | null>(null);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setDraft('');
    setMessages((prev) => [...prev, { id: `${Date.now()}-u`, from: 'user', text: trimmed }]);
    setSending(true);
    try {
      const res = await assistantApi.send(trimmed);
      const hasImport = !!res.pending_import && res.pending_import.length > 0;
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now()}-a`,
          from: 'assistant',
          text: res.reply,
          pendingImport: hasImport ? res.pending_import! : undefined,
          importStatus: hasImport ? 'pending' : undefined,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [...prev, { id: `${Date.now()}-e`, from: 'assistant', text: apiErrorMessage(err) }]);
    } finally {
      setSending(false);
    }
  };

  // Confirmar/cancelar la vista previa de "importar horario" (ver
  // pending_import en AssistantResponse) — /message del backend nunca
  // guarda nada por su cuenta, así que la confirmación en el chat es la
  // única acción que de verdad llama a POST /v1/assistant/schedule/import
  // (sección 4 del brief: "la IA recomienda, no impone").
  const confirmImport = async (messageId: string, items: ScheduleItem[]) => {
    setImportingId(messageId);
    try {
      const result = await assistantApi.importSchedule(items);
      setMessages((prev) => prev.map((m) => (m.id === messageId ? { ...m, importStatus: 'confirmed' } : m)));
      const partes: string[] = [];
      if (result.availability_created > 0) partes.push(`${result.availability_created} bloque(s) de disponibilidad`);
      if (result.events_created > 0) partes.push(`${result.events_created} evento(s)`);
      const resumen = partes.length ? `Listo, agregué ${partes.join(' y ')}.` : 'Listo, no había nada que agregar.';
      setMessages((prev) => [...prev, { id: `${Date.now()}-import-ok`, from: 'assistant', text: resumen }]);
    } catch (err) {
      setMessages((prev) => [...prev, { id: `${Date.now()}-import-err`, from: 'assistant', text: apiErrorMessage(err) }]);
    } finally {
      setImportingId(null);
    }
  };

  const cancelImport = (messageId: string) => {
    setMessages((prev) => prev.map((m) => (m.id === messageId ? { ...m, importStatus: 'cancelled' } : m)));
  };

  return (
    <Screen scroll={false} style={{ padding: 0 }}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>Asistente</Text>
        <Text style={styles.title}>Habla con tu día</Text>
      </View>

      <FlatList
        data={messages}
        keyExtractor={(m) => m.id}
        contentContainerStyle={styles.list}
        renderItem={({ item }) =>
          item.from === 'assistant' ? (
            <View>
              <View style={styles.assistantRow}>
                <View style={styles.assistantAvatar}>
                  <Ionicons name="sparkles" size={13} color={color.accent} />
                </View>
                <View style={[styles.bubble, styles.bubbleAssistant]}>
                  <Text style={styles.bubbleAssistantText}>{item.text}</Text>
                </View>
              </View>

              {item.pendingImport ? (
                <Card style={styles.importCard}>
                  {item.pendingImport.map((si, i) => (
                    <Text key={i} style={styles.importItem}>
                      {describeScheduleItem(si)}
                    </Text>
                  ))}
                  {item.importStatus === 'pending' ? (
                    <View style={styles.importActions}>
                      <Button
                        label="Sí, agrégalo"
                        onPress={() => confirmImport(item.id, item.pendingImport!)}
                        loading={importingId === item.id}
                      />
                      <View style={{ width: spacing.sm }} />
                      <Button label="Cancelar" variant="ghost" onPress={() => cancelImport(item.id)} />
                    </View>
                  ) : (
                    <Text style={styles.importResolvedText}>
                      {item.importStatus === 'confirmed' ? 'Agregado ✓' : 'No se agregó.'}
                    </Text>
                  )}
                </Card>
              ) : null}
            </View>
          ) : (
            <View style={[styles.bubble, styles.bubbleUser]}>
              <Text style={styles.bubbleUserText}>{item.text}</Text>
            </View>
          )
        }
      />

      <View style={styles.examplesRow}>
        {EXAMPLES.map((ex) => (
          <Text key={ex} style={styles.exampleChip} onPress={() => send(ex)}>
            {ex}
          </Text>
        ))}
      </View>

      <View style={styles.inputRow}>
        <View style={{ flex: 1 }}>
          <TextField
            label=""
            value={draft}
            onChangeText={setDraft}
            placeholder="Escribe un mensaje…"
            onSubmitEditing={() => send(draft)}
            style={styles.input}
          />
        </View>
        <View style={{ width: spacing.sm }} />
        <Button label="Enviar" onPress={() => send(draft)} loading={sending} disabled={!draft.trim()} />
      </View>
    </Screen>
  );
}
