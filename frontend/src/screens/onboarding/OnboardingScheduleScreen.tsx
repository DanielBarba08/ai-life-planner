import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { usersApi } from '../../api/endpoints';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Screen } from '../../components/Screen';
import { StepDots } from '../../components/StepDots';
import { TextField } from '../../components/TextField';
import { spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import type { OnboardingStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<OnboardingStackParamList, 'Horario'>;

const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;

export default function OnboardingScheduleScreen({ navigation }: Props) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        step: { ...type.caption, color: color.accent, textTransform: 'uppercase', marginTop: spacing.md },
        title: { ...type.display, color: color.ink, marginTop: spacing.sm, marginBottom: spacing.sm },
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.xl },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        spacer: { flex: 1, minHeight: spacing.lg },
      }),
    [color]
  );
  const { refreshUser } = useAuth();
  const [wake, setWake] = useState('07:00');
  const [sleep, setSleep] = useState('23:00');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const valid = HHMM.test(wake) && HHMM.test(sleep);

  const onNext = async () => {
    if (!valid) {
      setError('Usa el formato HH:MM, por ejemplo 07:00.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await usersApi.update({ wake_time: `${wake}:00`, sleep_time: `${sleep}:00` });
      await refreshUser();
      navigation.navigate('Preferencias');
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <StepDots total={4} current={1} />
      <Text style={styles.step}>Paso 1 de 4</Text>
      <Text style={styles.title}>¿Cuál es tu horario?</Text>
      <Text style={styles.subtitle}>
        Nunca vamos a planificar nada fuera de este rango — tu descanso siempre queda protegido.
      </Text>

      <TextField label="Me despierto a las" value={wake} onChangeText={setWake} placeholder="07:00" />
      <TextField label="Me duermo a las" value={sleep} onChangeText={setSleep} placeholder="23:00" />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <View style={styles.spacer} />
      <Button label="Continuar" onPress={onNext} loading={loading} disabled={!valid} />
    </Screen>
  );
}
