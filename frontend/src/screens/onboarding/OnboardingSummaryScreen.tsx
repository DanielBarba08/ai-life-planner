import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { usersApi } from '../../api/endpoints';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Screen } from '../../components/Screen';
import { StepDots } from '../../components/StepDots';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import type { OnboardingStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<OnboardingStackParamList, 'Resumen'>;

export default function OnboardingSummaryScreen({}: Props) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        step: { ...type.caption, color: color.accent, textTransform: 'uppercase', marginTop: spacing.md },
        checkCircle: {
          width: 44,
          height: 44,
          borderRadius: radius.pill,
          backgroundColor: color.good,
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: spacing.md,
        },
        title: { ...type.display, color: color.ink, marginTop: spacing.sm, marginBottom: spacing.sm },
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.lg },
        card: { marginBottom: spacing.xl },
        row: { ...type.body, color: color.muted, marginBottom: spacing.xs },
        value: { ...type.bodyStrong, color: color.ink },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
      }),
    [color]
  );
  const { user, refreshUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const finish = async () => {
    setError(null);
    setLoading(true);
    try {
      await usersApi.update({ onboarding_completed: true });
      await refreshUser();
      // Al refrescar el usuario, RootNavigator detecta onboarding_completed
      // === true y cambia solo a las pestañas principales — no hace falta
      // navegar manualmente a ningún lado desde aquí.
    } catch (err) {
      setError(apiErrorMessage(err));
      setLoading(false);
    }
  };

  return (
    <Screen>
      <StepDots total={4} current={4} />
      <Text style={styles.step}>Paso 4 de 4</Text>
      <View style={styles.checkCircle}>
        <Ionicons name="checkmark" size={22} color={color.accentInk} />
      </View>
      <Text style={styles.title}>Todo listo, {user?.name || 'bienvenido'}</Text>
      <Text style={styles.subtitle}>
        Puedes cambiar cualquiera de estos ajustes después, en cualquier momento — nada de esto queda fijo.
      </Text>

      <Card style={styles.card}>
        <Text style={styles.row}>
          Horario: <Text style={styles.value}>{user?.wake_time?.slice(0, 5)} – {user?.sleep_time?.slice(0, 5)}</Text>
        </Text>
        <Text style={styles.row}>
          Zona horaria: <Text style={styles.value}>{user?.timezone}</Text>
        </Text>
      </Card>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Button label="Empezar a usar AI Life Planner" onPress={finish} loading={loading} />
    </Screen>
  );
}
