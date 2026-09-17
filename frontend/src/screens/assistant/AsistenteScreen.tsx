import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { assistantApi } from '../../api/endpoints';
import { Button } from '../../components/Button';
import { Screen } from '../../components/Screen';
import { TextField } from '../../components/TextField';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';

interface ChatMessage {
  id: string;
  from: 'user' | 'assistant';
  text: string;
}

const EXAMPLES = ['Organiza mi tarde', '¿Qué hago ahora?', 'Optimiza mi día', 'No terminé las tareas de ayer'];

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
      }),
    [color, elevation]
  );
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      from: 'assistant',
      text: 'Puedo ayudarte con tu día real — prueba "optimiza mi día", "¿qué hago ahora?" o "quiero entrenar tres veces esta semana".',
    },
  ]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setDraft('');
    setMessages((prev) => [...prev, { id: `${Date.now()}-u`, from: 'user', text: trimmed }]);
    setSending(true);
    try {
      const res = await assistantApi.send(trimmed);
      setMessages((prev) => [...prev, { id: `${Date.now()}-a`, from: 'assistant', text: res.reply }]);
    } catch (err) {
      setMessages((prev) => [...prev, { id: `${Date.now()}-e`, from: 'assistant', text: apiErrorMessage(err) }]);
    } finally {
      setSending(false);
    }
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
            <View style={styles.assistantRow}>
              <View style={styles.assistantAvatar}>
                <Ionicons name="sparkles" size={13} color={color.accent} />
              </View>
              <View style={[styles.bubble, styles.bubbleAssistant]}>
                <Text style={styles.bubbleAssistantText}>{item.text}</Text>
              </View>
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
