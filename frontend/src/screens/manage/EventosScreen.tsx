import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { eventsApi } from '../../api/endpoints';
import type { FixedEvent } from '../../api/types';
import { BackHeader } from '../../components/BackHeader';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { EventFormModal } from '../../components/EventFormModal';
import { Screen } from '../../components/Screen';
import { useTheme } from '../../theme/ThemeContext';
import { radius, spacing, type } from '../../theme/tokens';
import { wallClockTime } from '../../utils/date';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'Eventos'>;

export default function EventosScreen({ navigation }: Props) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [formVisible, setFormVisible] = useState(false);
  const [editingEvent, setEditingEvent] = useState<FixedEvent | null>(null);

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.lg },
        muted: { ...type.body, color: color.muted },
        card: { marginBottom: spacing.sm },
        row: { flexDirection: 'row', alignItems: 'center' },
        iconCircle: {
          width: 30,
          height: 30,
          borderRadius: radius.pill,
          backgroundColor: color.surfaceAlt,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        eventTitle: { ...type.bodyStrong, color: color.ink },
        eventTime: { ...type.caption, color: color.muted, marginTop: 2 },
      }),
    [color]
  );

  const eventsQuery = useQuery<FixedEvent[]>({ queryKey: ['events'], queryFn: () => eventsApi.list() });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['events'] });
    setFormVisible(false);
    setEditingEvent(null);
  };

  const remove = async (id: string) => {
    await eventsApi.remove(id);
    queryClient.invalidateQueries({ queryKey: ['events'] });
  };

  return (
    <Screen>
      <BackHeader title="Eventos fijos" onBack={() => navigation.goBack()} />
      <Text style={styles.subtitle}>
        El Planning Engine nunca los mueve por su cuenta — son el marco fijo alrededor del cual acomoda tus tareas.
      </Text>

      <Button
        label="+ Nuevo evento"
        variant="secondary"
        onPress={() => {
          setEditingEvent(null);
          setFormVisible(true);
        }}
      />
      <View style={{ height: spacing.md }} />

      {eventsQuery.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (eventsQuery.data ?? []).length === 0 ? (
        <Card>
          <Text style={styles.muted}>No tienes eventos fijos todavía.</Text>
        </Card>
      ) : (
        (eventsQuery.data ?? []).map((e) => (
          <Card key={e.id} style={styles.card}>
            <Pressable
              onPress={() => {
                setEditingEvent(e);
                setFormVisible(true);
              }}
            >
              <View style={styles.row}>
                <View style={styles.iconCircle}>
                  <Ionicons name="calendar" size={14} color={color.muted} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.eventTitle}>{e.title}</Text>
                  <Text style={styles.eventTime}>
                    {e.start.slice(0, 10)} · {wallClockTime(e.start)} – {wallClockTime(e.end)}
                  </Text>
                </View>
                <Pressable onPress={() => remove(e.id)} hitSlop={8}>
                  <Ionicons name="trash-outline" size={17} color={color.muted} />
                </Pressable>
              </View>
            </Pressable>
          </Card>
        ))
      )}

      <EventFormModal
        visible={formVisible}
        onClose={() => {
          setFormVisible(false);
          setEditingEvent(null);
        }}
        onSaved={refresh}
        event={editingEvent}
      />
    </Screen>
  );
}
