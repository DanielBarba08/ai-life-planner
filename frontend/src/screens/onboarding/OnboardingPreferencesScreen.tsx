import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { preferencesApi } from '../../api/endpoints';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Screen } from '../../components/Screen';
import { StepDots } from '../../components/StepDots';
import { TextField } from '../../components/TextField';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import type { OnboardingStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<OnboardingStackParamList, 'Preferencias'>;

const HHMM = /^([01]\d|2[0-3]):[0-5]\d$/;

function RangeRow({
  icon,
  title,
  hint,
  start,
  end,
  onStart,
  onEnd,
  placeholderStart,
  placeholderEnd,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  hint: string;
  start: string;
  end: string;
  onStart: (v: string) => void;
  onEnd: (v: string) => void;
  placeholderStart: string;
  placeholderEnd: string;
}) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        rangeBlock: { marginBottom: spacing.md },
        rangeHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
        rangeIconCircle: {
          width: 30,
          height: 30,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        rangeTitle: { ...type.h2, color: color.ink },
        rangeHint: { ...type.caption, color: color.muted },
        rangeRow: { flexDirection: 'row' },
      }),
    [color]
  );
  return (
    <Card style={styles.rangeBlock}>
      <View style={styles.rangeHeader}>
        <View style={styles.rangeIconCircle}>
          <Ionicons name={icon} size={16} color={color.accent} />
        </View>
        <View>
          <Text style={styles.rangeTitle}>{title}</Text>
          <Text style={styles.rangeHint}>{hint}</Text>
        </View>
      </View>
      <View style={styles.rangeRow}>
        <View style={{ flex: 1 }}>
          <TextField label="Desde" value={start} onChangeText={onStart} placeholder={placeholderStart} />
        </View>
        <View style={{ width: spacing.md }} />
        <View style={{ flex: 1 }}>
          <TextField label="Hasta" value={end} onChangeText={onEnd} placeholder={placeholderEnd} />
        </View>
      </View>
    </Card>
  );
}

export default function OnboardingPreferencesScreen({ navigation }: Props) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        step: { ...type.caption, color: color.accent, textTransform: 'uppercase', marginTop: spacing.md },
        title: { ...type.display, color: color.ink, marginTop: spacing.sm, marginBottom: spacing.sm },
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.lg },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
      }),
    [color]
  );
  const [focusStart, setFocusStart] = useState('');
  const [focusEnd, setFocusEnd] = useState('');
  const [studyStart, setStudyStart] = useState('');
  const [studyEnd, setStudyEnd] = useState('');
  const [workoutStart, setWorkoutStart] = useState('');
  const [workoutEnd, setWorkoutEnd] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const rangeValid = (s: string, e: string) => (!s && !e) || (HHMM.test(s) && HHMM.test(e));
  const allValid = rangeValid(focusStart, focusEnd) && rangeValid(studyStart, studyEnd) && rangeValid(workoutStart, workoutEnd);

  const submit = async () => {
    if (!allValid) {
      setError('Revisa los horarios — usa el formato HH:MM o deja ambos campos vacíos.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await preferencesApi.put({
        preferred_focus_hours: focusStart && focusEnd ? [{ start: focusStart, end: focusEnd }] : [],
        preferred_study_hours: studyStart && studyEnd ? [{ start: studyStart, end: studyEnd }] : [],
        preferred_workout_hours: workoutStart && workoutEnd ? [{ start: workoutStart, end: workoutEnd }] : [],
      });
      navigation.navigate('Disponibilidad');
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <StepDots total={4} current={2} />
      <Text style={styles.step}>Paso 2 de 4</Text>
      <Text style={styles.title}>¿Cuándo rindes mejor?</Text>
      <Text style={styles.subtitle}>
        Opcional — pero si nos dices a qué horas prefieres concentrarte, estudiar o entrenar, "Optimizar mi día"
        va a intentar poner esas tareas justo ahí. Puedes cambiar esto cuando quieras desde Ajustes.
      </Text>

      <RangeRow
        icon="bulb-outline"
        title="Concentración"
        hint="Tareas que requieren enfoque profundo"
        start={focusStart}
        end={focusEnd}
        onStart={setFocusStart}
        onEnd={setFocusEnd}
        placeholderStart="09:00"
        placeholderEnd="12:00"
      />
      <RangeRow
        icon="book-outline"
        title="Estudio"
        hint="Tareas de estudio"
        start={studyStart}
        end={studyEnd}
        onStart={setStudyStart}
        onEnd={setStudyEnd}
        placeholderStart="16:00"
        placeholderEnd="18:00"
      />
      <RangeRow
        icon="barbell-outline"
        title="Entrenamiento"
        hint="Ejercicio físico"
        start={workoutStart}
        end={workoutEnd}
        onStart={setWorkoutStart}
        onEnd={setWorkoutEnd}
        placeholderStart="18:30"
        placeholderEnd="19:30"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Button label="Continuar" onPress={submit} loading={loading} disabled={!allValid} />
    </Screen>
  );
}
