import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { availabilityApi } from '../../api/endpoints';
import type { AvailabilityBlock } from '../../api/types';
import { AvailabilityFormModal } from '../../components/AvailabilityFormModal';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Screen } from '../../components/Screen';
import { StepDots } from '../../components/StepDots';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import type { OnboardingStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<OnboardingStackParamList, 'Disponibilidad'>;

const DAY_LABEL = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
const TYPE_LABEL: Record<string, string> = { trabajo: 'Trabajo', escuela: 'Escuela', personal: 'Personal', otro: 'Otro' };
const TYPE_ICON: Record<string, keyof typeof Ionicons.glyphMap> = {
  trabajo: 'briefcase-outline',
  escuela: 'school-outline',
  personal: 'person-outline',
  otro: 'ellipsis-horizontal-outline',
};

/**
 * Paso opcional del onboarding (pedido por Daniel como mejora de UX, no un
 * hueco de datos — el endpoint y la pantalla en Ajustes → Disponibilidad ya
 * existían). Reutiliza el mismo `AvailabilityFormModal` que esa pantalla en
 * vez de duplicar el formulario, y "Continuar" avanza sin exigir nada: es
 * opcional de verdad, no un paso disfrazado de obligatorio.
 */
export default function OnboardingAvailabilityScreen({ navigation }: Props) {
  const { color } = useTheme();
  const queryClient = useQueryClient();
  const [formVisible, setFormVisible] = useState(false);

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        step: { ...type.caption, color: color.accent, textTransform: 'uppercase', marginTop: spacing.md },
        title: { ...type.display, color: color.ink, marginTop: spacing.sm, marginBottom: spacing.sm },
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
        spacer: { minHeight: spacing.lg },
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
      <StepDots total={4} current={3} />
      <Text style={styles.step}>Paso 3 de 4</Text>
      <Text style={styles.title}>¿Tienes horarios fijos?</Text>
      <Text style={styles.subtitle}>
        Opcional — trabajo, escuela o cualquier otro bloque recurrente. "Optimizar mi día" nunca va a poner tareas
        ahí. Puedes agregar, editar o borrar esto cuando quieras desde Ajustes, así que si no tienes nada a la mano
        ahora, puedes continuar sin agregar nada.
      </Text>

      <Button label="+ Agregar bloque" variant="secondary" onPress={() => setFormVisible(true)} />
      <View style={{ height: spacing.md }} />

      {query.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (query.data ?? []).length === 0 ? (
        <Card>
          <Text style={styles.muted}>Sin bloques todavía — puedes seguir sin agregar ninguno.</Text>
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

      <View style={styles.spacer} />
      <Button label="Continuar" onPress={() => navigation.navigate('Resumen')} />

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
