import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { allHalfHourOptions } from '../utils/date';

const OPTIONS = allHalfHourOptions();

/**
 * Selector de hora de un clic — pedido por Daniel el 17 nov para Eventos
 * fijos y Disponibilidad ("hacer un seleccionador con todas las horas
 * posibles y el usuario pueda seleccionar la hora, no escribirla"). A
 * diferencia de TimeOptionsField (usado en Tareas), que ofrece solo unas
 * cuantas horas sugeridas con una opción "Personalizada" que sigue
 * permitiendo teclear, este selector cubre TODA la lista (cada media hora,
 * de 00:00 a 23:30) y no tiene ninguna forma de escribir una hora a mano.
 */
export function TimePickerField({
  label,
  value,
  onChange,
  placeholder = 'Elegir hora',
}: {
  label: string;
  /** Hora "HH:MM", o '' si no hay ninguna elegida. */
  value: string;
  onChange: (hhmm: string) => void;
  placeholder?: string;
}) {
  const { color, elevation } = useTheme();
  const [open, setOpen] = useState(false);

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        wrap: { marginBottom: spacing.md },
        fieldLabel: { ...type.caption, color: color.muted, marginBottom: spacing.xs, textTransform: 'uppercase' },
        field: {
          flexDirection: 'row',
          alignItems: 'center',
          borderWidth: 1,
          borderColor: color.line,
          borderRadius: radius.md,
          paddingHorizontal: spacing.md,
          paddingVertical: 12,
          backgroundColor: color.surface,
        },
        fieldText: { ...type.body, color: value ? color.ink : color.muted, flex: 1 },
        backdrop: { flex: 1, backgroundColor: 'rgba(20,20,16,0.4)', alignItems: 'center', justifyContent: 'center' },
        card: {
          width: 300,
          maxWidth: '90%',
          maxHeight: '72%',
          backgroundColor: color.surface,
          borderRadius: radius.lg,
          padding: spacing.lg,
          ...elevation.raised,
        },
        header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
        headerLabel: { ...type.h2, color: color.ink },
        grid: { flexDirection: 'row', flexWrap: 'wrap' },
        optionWrap: { width: '25%', paddingHorizontal: 3, marginBottom: spacing.sm },
        option: { borderRadius: radius.md, paddingVertical: 8, alignItems: 'center', backgroundColor: color.surfaceAlt },
        optionSelected: { backgroundColor: color.accent },
        optionText: { ...type.caption, color: color.ink },
        optionTextSelected: { color: color.accentInk },
        footer: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: color.line },
        footerLabel: { ...type.bodyStrong, color: color.accent },
      }),
    [color, elevation, value]
  );

  return (
    <View style={styles.wrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Pressable style={styles.field} onPress={() => setOpen(true)}>
        <Ionicons name="time-outline" size={16} color={color.muted} style={{ marginRight: spacing.sm }} />
        <Text style={styles.fieldText}>{value || placeholder}</Text>
      </Pressable>

      <Modal visible={open} animationType="fade" transparent onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          <Pressable style={styles.card} onPress={() => {}}>
            <View style={styles.header}>
              <Text style={styles.headerLabel}>{label}</Text>
            </View>

            <ScrollView>
              <View style={styles.grid}>
                {OPTIONS.map((opt) => {
                  const isSelected = opt === value;
                  return (
                    <View key={opt} style={styles.optionWrap}>
                      <Pressable
                        style={[styles.option, isSelected && styles.optionSelected]}
                        onPress={() => {
                          onChange(opt);
                          setOpen(false);
                        }}
                      >
                        <Text style={[styles.optionText, isSelected && styles.optionTextSelected]}>{opt}</Text>
                      </Pressable>
                    </View>
                  );
                })}
              </View>
            </ScrollView>

            <View style={styles.footer}>
              <Pressable onPress={() => setOpen(false)}>
                <Text style={styles.footerLabel}>Cerrar</Text>
              </Pressable>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}
