import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Screen } from '../../components/Screen';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'AjustesHome'>;

const MANAGE_ROWS: { icon: keyof typeof Ionicons.glyphMap; label: string; hint: string; screen: keyof AjustesStackParamList }[] = [
  { icon: 'checkmark-done-outline', label: 'Tareas', hint: 'Crear, editar y borrar', screen: 'Tareas' },
  { icon: 'calendar-outline', label: 'Eventos fijos', hint: 'Lo que ya tienes agendado', screen: 'Eventos' },
  { icon: 'flag-outline', label: 'Objetivos', hint: 'Metas de hoy, la semana o más allá', screen: 'Objetivos' },
  { icon: 'repeat-outline', label: 'Disponibilidad', hint: 'Bloques recurrentes de trabajo/escuela', screen: 'Disponibilidad' },
  { icon: 'sync-outline', label: 'Hábitos', hint: 'Metas recurrentes, con progreso real de la semana', screen: 'Habitos' },
];

export default function AjustesScreen({ navigation }: Props) {
  const { user, logout } = useAuth();
  const { color, mode, setMode } = useTheme();
  const initial = (user?.name || user?.email || '?').trim().charAt(0).toUpperCase();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        eyebrow: { ...type.caption, color: color.accent, textTransform: 'uppercase' },
        title: { ...type.display, color: color.ink, marginTop: spacing.xs, marginBottom: spacing.lg },
        avatarRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg },
        avatar: {
          width: 52,
          height: 52,
          borderRadius: radius.pill,
          backgroundColor: color.accent,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.md,
        },
        avatarText: { ...type.h1, color: color.accentInk },
        avatarName: { ...type.h2, color: color.ink },
        avatarEmail: { ...type.caption, color: color.muted, marginTop: 2 },
        sectionTitle: { ...type.caption, color: color.muted, textTransform: 'uppercase', marginBottom: spacing.sm },
        card: { marginBottom: spacing.md },
        manageRow: {
          flexDirection: 'row',
          alignItems: 'center',
          marginBottom: spacing.sm,
          paddingBottom: spacing.sm,
          borderBottomWidth: 1,
          borderBottomColor: color.line,
        },
        manageRowLast: { borderBottomWidth: 0, marginBottom: 0, paddingBottom: 0 },
        manageHint: { ...type.caption, color: color.muted, marginTop: 2 },
        rowIconCircle: {
          width: 30,
          height: 30,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        rowValue: { ...type.bodyStrong, color: color.ink, marginTop: 2 },
        planHeader: { flexDirection: 'row', alignItems: 'center' },
        planLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase', marginLeft: spacing.xs },
        planValue: { ...type.h1, color: color.ink, marginTop: 2, marginBottom: spacing.sm },
        planHint: { ...type.caption, color: color.muted },
        appearanceRow: {
          flexDirection: 'row',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: spacing.sm,
          paddingBottom: spacing.sm,
          borderBottomWidth: 1,
          borderBottomColor: color.line,
        },
        appearanceRowLast: { borderBottomWidth: 0, marginBottom: 0, paddingBottom: 0 },
        appearanceLabel: { ...type.bodyStrong, color: color.muted },
        appearanceLabelActive: { color: color.accent },
      }),
    [color]
  );

  return (
    <Screen>
      <Text style={styles.eyebrow}>Ajustes</Text>
      <Text style={styles.title}>Tu cuenta</Text>

      <View style={styles.avatarRow}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{initial}</Text>
        </View>
        <View>
          <Text style={styles.avatarName}>{user?.name || 'Sin nombre'}</Text>
          <Text style={styles.avatarEmail}>{user?.email}</Text>
        </View>
      </View>

      <Card style={styles.card}>
        <Row icon="calendar-outline" label="Zona horaria" value={user?.timezone || '—'} />
        <Row
          icon="time-outline"
          label="Horario"
          value={`${user?.wake_time?.slice(0, 5) ?? '—'} – ${user?.sleep_time?.slice(0, 5) ?? '—'}`}
          last
          centered
        />
      </Card>

      <Text style={styles.sectionTitle}>Gestionar</Text>
      <Card style={styles.card}>
        {MANAGE_ROWS.map((row, i) => (
          <Pressable key={row.screen} onPress={() => navigation.navigate(row.screen)}>
            <View style={[styles.manageRow, i === MANAGE_ROWS.length - 1 && styles.manageRowLast]}>
              <View style={styles.rowIconCircle}>
                <Ionicons name={row.icon} size={15} color={color.accent} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowValue}>{row.label}</Text>
                <Text style={styles.manageHint}>{row.hint}</Text>
              </View>
              <Ionicons name="chevron-forward" size={16} color={color.muted} />
            </View>
          </Pressable>
        ))}
      </Card>

      <Pressable onPress={() => navigation.navigate('ComoDecide')}>
        <Card style={styles.card}>
          <View style={[styles.manageRow, styles.manageRowLast]}>
            <View style={styles.rowIconCircle}>
              <Ionicons name="flask-outline" size={15} color={color.accent} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowValue}>Cómo decide tus horarios</Text>
              <Text style={styles.manageHint}>Reglas generales del motor, con evidencia científica real</Text>
            </View>
            <Ionicons name="chevron-forward" size={16} color={color.muted} />
          </View>
        </Card>
      </Pressable>

      <Text style={styles.sectionTitle}>Apariencia</Text>
      <Card style={styles.card}>
        {(
          [
            { key: 'system' as const, label: 'Sistema' },
            { key: 'light' as const, label: 'Claro' },
            { key: 'dark' as const, label: 'Oscuro' },
          ]
        ).map((opt, i, arr) => {
          const active = mode === opt.key;
          return (
            <Pressable key={opt.key} onPress={() => setMode(opt.key)}>
              <View style={[styles.appearanceRow, i === arr.length - 1 && styles.appearanceRowLast]}>
                <Text style={[styles.appearanceLabel, active && styles.appearanceLabelActive]}>{opt.label}</Text>
                {active ? <Ionicons name="checkmark" size={18} color={color.accent} /> : null}
              </View>
            </Pressable>
          );
        })}
      </Card>

      <Card style={styles.card}>
        <View style={styles.planHeader}>
          <Ionicons name="star" size={16} color={color.streak} />
          <Text style={styles.planLabel}>Plan actual</Text>
        </View>
        <Text style={styles.planValue}>Free</Text>
        <Text style={styles.planHint}>
          Premium ($200 MXN/mes, precio provisional) todavía no tiene flujo de pago en esta versión — llega con la
          integración de Stripe (sección K del blueprint).
        </Text>
      </Card>

      <Button label="Cerrar sesión" variant="ghost" onPress={logout} />
    </Screen>
  );
}

function Row({
  icon,
  label,
  value,
  last,
  centered,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  value: string;
  last?: boolean;
  centered?: boolean;
}) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        row: {
          flexDirection: 'row',
          alignItems: 'center',
          marginBottom: spacing.sm,
          paddingBottom: spacing.sm,
          borderBottomWidth: 1,
          borderBottomColor: color.line,
        },
        rowIconCircle: {
          width: 30,
          height: 30,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        rowLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase' },
        rowValue: { ...type.bodyStrong, color: color.ink, marginTop: 2 },
        rowTextWrapCentered: { flex: 1, alignItems: 'center' },
        rowLabelCentered: { textAlign: 'center' },
        rowValueCentered: { textAlign: 'center' },
      }),
    [color]
  );
  return (
    <View style={[styles.row, last && { borderBottomWidth: 0, marginBottom: 0, paddingBottom: 0 }]}>
      <View style={styles.rowIconCircle}>
        <Ionicons name={icon} size={15} color={color.accent} />
      </View>
      {/* "Horario" (pedido por Daniel) se centra en el espacio que queda
      junto al ícono, en vez de quedar pegado a la izquierda justo después
      de él — el resto de filas (ej. "Zona horaria") sigue igual. */}
      <View style={centered ? styles.rowTextWrapCentered : undefined}>
        <Text style={[styles.rowLabel, centered && styles.rowLabelCentered]}>{label}</Text>
        <Text style={[styles.rowValue, centered && styles.rowValueCentered]}>{value}</Text>
      </View>
    </View>
  );
}
