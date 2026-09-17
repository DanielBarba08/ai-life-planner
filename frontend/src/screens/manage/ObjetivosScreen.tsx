import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { goalsApi } from '../../api/endpoints';
import type { Goal, GoalStatus } from '../../api/types';
import { BackHeader } from '../../components/BackHeader';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { GoalFormModal } from '../../components/GoalFormModal';
import { Pill } from '../../components/Pill';
import { Screen } from '../../components/Screen';
import { useTheme } from '../../theme/ThemeContext';
import { radius, spacing, type } from '../../theme/tokens';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'Objetivos'>;

const HORIZON_LABEL: Record<string, string> = { hoy: 'Hoy', semana: 'Esta semana', mes: 'Este mes', largo_plazo: 'Largo plazo' };

export default function ObjetivosScreen({ navigation }: Props) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [formVisible, setFormVisible] = useState(false);
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);

  const statusColor: Record<GoalStatus, { fg: string; bg: string }> = React.useMemo(
    () => ({
      activo: { fg: color.accent, bg: color.accentSoft },
      completado: { fg: color.good, bg: color.goodSoft },
      archivado: { fg: color.muted, bg: color.surfaceAlt },
    }),
    [color]
  );

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
        goalTitle: { ...type.bodyStrong, color: color.ink, marginBottom: spacing.xs },
        metaRow: { flexDirection: 'row', alignItems: 'center' },
        horizon: { ...type.caption, color: color.muted, marginLeft: spacing.sm },
      }),
    [color]
  );

  const goalsQuery = useQuery<Goal[]>({ queryKey: ['goals'], queryFn: () => goalsApi.list() });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['goals'] });
    setFormVisible(false);
    setEditingGoal(null);
  };

  const remove = async (id: string) => {
    await goalsApi.remove(id);
    queryClient.invalidateQueries({ queryKey: ['goals'] });
  };

  return (
    <Screen>
      <BackHeader title="Objetivos" onBack={() => navigation.goBack()} />
      <Text style={styles.subtitle}>
        Incluye los que has creado aquí y los que confirmaste con el asistente (por ejemplo, "quiero entrenar tres veces esta semana").
      </Text>

      <Button
        label="+ Nuevo objetivo"
        variant="secondary"
        onPress={() => {
          setEditingGoal(null);
          setFormVisible(true);
        }}
      />
      <View style={{ height: spacing.md }} />

      {goalsQuery.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (goalsQuery.data ?? []).length === 0 ? (
        <Card>
          <Text style={styles.muted}>No tienes objetivos todavía.</Text>
        </Card>
      ) : (
        (goalsQuery.data ?? []).map((g) => (
          <Card key={g.id} style={styles.card}>
            <Pressable
              onPress={() => {
                setEditingGoal(g);
                setFormVisible(true);
              }}
            >
              <View style={styles.row}>
                <View style={styles.iconCircle}>
                  <Ionicons name="flag" size={14} color={color.accent} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.goalTitle}>{g.title}</Text>
                  <View style={styles.metaRow}>
                    <Pill label={g.status} fg={statusColor[g.status].fg} bg={statusColor[g.status].bg} />
                    <Text style={styles.horizon}>{HORIZON_LABEL[g.horizon] ?? g.horizon}</Text>
                  </View>
                </View>
                <Pressable onPress={() => remove(g.id)} hitSlop={8}>
                  <Ionicons name="trash-outline" size={17} color={color.muted} />
                </Pressable>
              </View>
            </Pressable>
          </Card>
        ))
      )}

      <GoalFormModal
        visible={formVisible}
        onClose={() => {
          setFormVisible(false);
          setEditingGoal(null);
        }}
        onSaved={refresh}
        goal={editingGoal}
      />
    </Screen>
  );
}
