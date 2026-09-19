import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { availabilityApi } from '../../api/endpoints';
import type { AvailabilityBlock } from '../../api/types';
import { AvailabilityFormModal } from '../../components/AvailabilityFormModal';
import { BackHeader } from '../../components/BackHeader';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Screen } from '../../components/Screen';
import { useTheme } from '../../theme/ThemeContext';
import { radius, spacing, type } from '../../theme/tokens';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'Disponibilidad'>;

const DAY_LABEL = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const TYPE_LABEL: Record<string, string> = {
  trabajo: 'Trabajo',
  escuela: 'Escuela',
  personal: 'Personal',
  comida: 'Comida',
  aseo: 'Aseo',
  descanso: 'Descanso',
  otro: 'Otro',
};
const TYPE_ICON: Record<string, keyof typeof Ionicons.glyphMap> = {
  trabajo: 'briefcase-outline',
  escuela: 'school-outline',
  personal: 'person-outline',
  comida: 'restaurant-outline',
  aseo: 'water-outline',
  descanso: 'moon-outline',
  otro: 'ellipsis-horizontal-outline',
};

export default function DisponibilidadScreen({ navigation }: Props) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [formVisible, setFormVisible] = useState(false);

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
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        blockTitle: { ...type.bodyStrong, color: color.ink },
        blockTime: { ...type.caption, color: color.muted, marginTop: 2 },
      }),
    [color]
  );

  const query = useQuery<AvailabilityBlock[]>({ queryKey: ['availability'], queryFn: () => availabilityApi.list() });

  const remove = async (id: string) => {
    await availabilityApi.remove(id);
    queryClient.invalidateQueries({ queryKey: ['availability'] });
  };

  return (
    <Screen>
      <BackHeader title="Disponibilidad" onBack={() => navigation.goBack()} />
      <Text style={styles.subtitle}>
        Bloques recurrentes de trabajo, escuela, comida, aseo o descanso — "Optimizar mi día" nunca pone tareas ahí, cada semana, sin que tengas que repetirlo.
      </Text>

      <Button label="+ Nuevo bloque" variant="secondary" onPress={() => setFormVisible(true)} />
      <View style={{ height: spacing.md }} />

      {query.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (query.data ?? []).length === 0 ? (
        <Card>
          <Text style={styles.muted}>No tienes bloques de disponibilidad recurrente todavía.</Text>
        </Card>
      ) : (
        (query.data ?? []).map((b) => (
          <Card key={b.id} style={styles.card}>
            <View style={styles.row}>
              <View style={styles.iconCircle}>
                <Ionicons name={TYPE_ICON[b.type] ?? 'time-outline'} size={14} color={color.accent} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.blockTitle}>
                  {TYPE_LABEL[b.type] ?? b.type} · {DAY_LABEL[b.day_of_week]}
                </Text>
                <Text style={styles.blockTime}>
                  {b.start.slice(0, 5)} – {b.end.slice(0, 5)}
                </Text>
              </View>
              <Pressable onPress={() => remove(b.id)} hitSlop={8}>
                <Ionicons name="trash-outline" size={17} color={color.muted} />
              </Pressable>
            </View>
          </Card>
        ))
      )}

      <AvailabilityFormModal
        visible={formVisible}
        onClose={() => setFormVisible(false)}
        onSaved={() => {
          setFormVisible(false);
          queryClient.invalidateQueries({ queryKey: ['availability'] });
        }}
      />
    </Screen>
  );
}
