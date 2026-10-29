import { Ionicons } from '@expo/vector-icons';
import React, { useState } from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { mediumDateLabel, monthGrid, monthYearLabel, todayIsoDate } from '../utils/date';

const WEEKDAY_HEADERS = ['L', 'M', 'M', 'J', 'V', 'S', 'D'];
const TODAY = todayIsoDate();

/**
 * Selector de fecha de un clic — pedido por Daniel (28 oct) para
 * reemplazar los campos de texto libre de fecha ("2026-09-20" tecleado a
 * mano, fácil de equivocar) en el formulario de tareas. Muestra un campo
 * tipo TextField que al tocarlo abre un calendario de mes para elegir el
 * día — nunca texto escrito. Genérico (no es específico de tareas) para
 * poder reusarse luego en Eventos/Disponibilidad si se pide.
 */
export function DatePickerField({
  label,
  value,
  onChange,
  onClear,
  placeholder = 'Elegir fecha',
}: {
  label: string;
  /** Fecha ISO "YYYY-MM-DD", o '' si no hay ninguna elegida. */
  value: string;
  onChange: (iso: string) => void;
  /** Si se da, el campo muestra una "x" para volver a '' cuando ya hay fecha. */
  onClear?: () => void;
  placeholder?: string;
}) {
  const { color, elevation } = useTheme();
  const [open, setOpen] = useState(false);
  const base = value || TODAY;
  const [y, m] = base.split('-').map(Number);
  const [viewYear, setViewYear] = useState(y);
  const [viewMonth, setViewMonth] = useState(m - 1);

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
        clearBtn: { marginLeft: spacing.sm },
        backdrop: { flex: 1, backgroundColor: 'rgba(20,20,16,0.4)', alignItems: 'center', justifyContent: 'center' },
        card: {
          width: 320,
          maxWidth: '90%',
          backgroundColor: color.surface,
          borderRadius: radius.lg,
          padding: spacing.lg,
          ...elevation.raised,
        },
        header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
        headerLabel: { ...type.h2, color: color.ink, textTransform: 'capitalize' },
        navBtn: { padding: spacing.xs },
        weekRow: { flexDirection: 'row', marginBottom: spacing.xs },
        weekdayCell: { width: 36, alignItems: 'center' },
        weekdayText: { ...type.caption, color: color.muted },
        grid: { flexDirection: 'row', flexWrap: 'wrap' },
        dayCell: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center', marginBottom: 2 },
        dayCircle: { width: 32, height: 32, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center' },
        dayCircleToday: { borderWidth: 1, borderColor: color.accent },
        dayCircleSelected: { backgroundColor: color.accent },
        dayText: { ...type.body, color: color.ink },
        dayTextSelected: { color: color.accentInk },
        footer: { flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.md, paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: color.line },
        footerLabel: { ...type.bodyStrong, color: color.accent },
      }),
    [color, elevation, value]
  );

  const openPicker = () => {
    const b = value || TODAY;
    const [yy, mm] = b.split('-').map(Number);
    setViewYear(yy);
    setViewMonth(mm - 1);
    setOpen(true);
  };

  const shiftMonth = (delta: number) => {
    let nm = viewMonth + delta;
    let ny = viewYear;
    if (nm < 0) {
      nm = 11;
      ny -= 1;
    } else if (nm > 11) {
      nm = 0;
      ny += 1;
    }
    setViewMonth(nm);
    setViewYear(ny);
  };

  const cells = monthGrid(viewYear, viewMonth);

  return (
    <View style={styles.wrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Pressable style={styles.field} onPress={openPicker}>
        <Ionicons name="calendar-outline" size={16} color={color.muted} style={{ marginRight: spacing.sm }} />
        <Text style={styles.fieldText}>{value ? mediumDateLabel(value) : placeholder}</Text>
        {value && onClear ? (
          <Pressable onPress={onClear} hitSlop={8} style={styles.clearBtn}>
            <Ionicons name="close-circle" size={18} color={color.muted} />
          </Pressable>
        ) : null}
      </Pressable>

      <Modal visible={open} animationType="fade" transparent onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          <Pressable style={styles.card} onPress={() => {}}>
            <View style={styles.header}>
              <Pressable style={styles.navBtn} onPress={() => shiftMonth(-1)} hitSlop={8}>
                <Ionicons name="chevron-back" size={20} color={color.ink} />
              </Pressable>
              <Text style={styles.headerLabel}>{monthYearLabel(viewYear, viewMonth)}</Text>
              <Pressable style={styles.navBtn} onPress={() => shiftMonth(1)} hitSlop={8}>
                <Ionicons name="chevron-forward" size={20} color={color.ink} />
              </Pressable>
            </View>

            <View style={styles.weekRow}>
              {WEEKDAY_HEADERS.map((w, i) => (
                <View key={i} style={styles.weekdayCell}>
                  <Text style={styles.weekdayText}>{w}</Text>
                </View>
              ))}
            </View>

            <View style={styles.grid}>
              {cells.map((iso, i) => {
                if (!iso) return <View key={i} style={styles.dayCell} />;
                const isToday = iso === TODAY;
                const isSelected = iso === value;
                return (
                  <Pressable
                    key={i}
                    style={styles.dayCell}
                    onPress={() => {
                      onChange(iso);
                      setOpen(false);
                    }}
                  >
                    <View style={[styles.dayCircle, isToday && styles.dayCircleToday, isSelected && styles.dayCircleSelected]}>
                      <Text style={[styles.dayText, isSelected && styles.dayTextSelected]}>{Number(iso.slice(-2))}</Text>
                    </View>
                  </Pressable>
                );
              })}
            </View>

            <View style={styles.footer}>
              <Pressable
                onPress={() => {
                  onChange(TODAY);
                  setOpen(false);
                }}
              >
                <Text style={styles.footerLabel}>Hoy</Text>
              </Pressable>
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
