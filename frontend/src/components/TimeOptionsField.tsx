import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { spacing, type } from '../theme/tokens';
import { Pill } from './Pill';
import { TextField } from './TextField';

const DEFAULT_OPTIONS = ['08:00', '09:00', '12:00', '14:00', '16:00', '18:00', '20:00', '21:00'];
const CUSTOM_KEY = '__custom__';

/**
 * Selector de hora por pestañas (pills) — pedido por Daniel (28 oct) para
 * reemplazar el campo de texto libre de hora ("18:00" tecleado a mano) en
 * el formulario de tareas. Si la hora no está entre las opciones
 * establecidas (por ejemplo al editar una tarea con hora ya guardada como
 * "14:30"), se activa sola la opción "Personalizada" con un campo de texto
 * — para no perder la posibilidad de una hora exacta que no esté en la
 * lista.
 */
export function TimeOptionsField({
  label,
  value,
  onChange,
  options = DEFAULT_OPTIONS,
}: {
  label: string;
  /** Hora "HH:MM", o '' si no hay ninguna elegida. */
  value: string;
  onChange: (hhmm: string) => void;
  options?: string[];
}) {
  const { color } = useTheme();
  const isCustom = !!value && !options.includes(value);
  const [showCustomInput, setShowCustomInput] = useState(isCustom);

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        wrap: { marginBottom: spacing.md },
        fieldLabel: { ...type.caption, color: color.muted, marginBottom: spacing.sm, textTransform: 'uppercase' },
        row: { flexDirection: 'row', flexWrap: 'wrap' },
        pillWrap: { marginRight: spacing.sm, marginBottom: spacing.sm },
      }),
    [color]
  );

  return (
    <View style={styles.wrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.row}>
        {options.map((opt) => (
          <Pressable
            key={opt}
            style={styles.pillWrap}
            onPress={() => {
              setShowCustomInput(false);
              onChange(opt);
            }}
          >
            <Pill
              label={opt}
              fg={value === opt ? color.accentInk : color.muted}
              bg={value === opt ? color.accent : color.surfaceAlt}
            />
          </Pressable>
        ))}
        <Pressable
          key={CUSTOM_KEY}
          style={styles.pillWrap}
          onPress={() => {
            setShowCustomInput(true);
            if (!isCustom) onChange('');
          }}
        >
          <Pill
            label="Personalizada"
            fg={showCustomInput ? color.accentInk : color.muted}
            bg={showCustomInput ? color.accent : color.surfaceAlt}
          />
        </Pressable>
      </View>

      {showCustomInput ? (
        <TextField
          label="Hora exacta (HH:MM)"
          value={value}
          onChangeText={onChange}
          placeholder="14:30"
          keyboardType="numbers-and-punctuation"
        />
      ) : null}
    </View>
  );
}
