import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import type { PlanBlock } from '../api/types';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { dayProgressMinutes, formatDurationMin, friendlyDate, greeting } from '../utils/date';

interface HeroProps {
  blocks: PlanBlock[];
  streak: number | undefined;
  hasPlanToday: boolean;
}

/**
 * Encabezado de "Mi día" — sección de diseño pedida por Daniel: que la app
 * se sienta lo bastante atractiva como para que la gente entre todos los
 * días, sin dejar de verse profesional (base tipo Things 3 / Fantastical +
 * un par de elementos de enganche, no un juego completo).
 *
 * Dos señales reales, nunca inventadas:
 * - Racha: viene de GET /v1/planning/streak (días consecutivos con un plan
 *   generado de verdad, ver backend/app/planning/service.py::compute_streak).
 * - Progreso del día: calculado de los bloques reales de hoy vs. la hora
 *   actual del dispositivo (dayProgressMinutes) — no una barra decorativa.
 */
export function Hero({ blocks, streak, hasPlanToday }: HeroProps) {
  const { color, elevation } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        hero: {
          borderRadius: radius.xl,
          padding: spacing.lg,
          marginBottom: spacing.md,
        },
        greeting: { ...type.caption, color: 'rgba(255,255,255,0.85)', textTransform: 'uppercase' },
        date: { ...type.display, color: color.accentInk, marginTop: spacing.xs, marginBottom: spacing.md },
        row: { flexDirection: 'row', flexWrap: 'wrap' },
        streakPill: {
          flexDirection: 'row',
          alignItems: 'center',
          backgroundColor: 'rgba(255,255,255,0.16)',
          borderRadius: radius.pill,
          paddingVertical: spacing.xs,
          paddingHorizontal: spacing.sm,
        },
        streakText: { ...type.caption, color: color.accentInk, marginLeft: spacing.xs },
        progressBlock: { marginTop: spacing.md },
        progressTrack: {
          height: 8,
          borderRadius: radius.pill,
          backgroundColor: 'rgba(255,255,255,0.22)',
          overflow: 'hidden',
        },
        progressFill: {
          height: '100%',
          borderRadius: radius.pill,
          backgroundColor: color.accentInk,
        },
        progressLabel: { ...type.caption, color: 'rgba(255,255,255,0.85)', marginTop: spacing.xs },
      }),
    [color]
  );
  const { doneMin, totalMin } = dayProgressMinutes(blocks);
  const pct = totalMin > 0 ? Math.min(1, doneMin / totalMin) : 0;
  const showStreak = typeof streak === 'number' && streak > 0;

  return (
    <LinearGradient
      colors={[color.heroGradientStart, color.heroGradientEnd]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={[styles.hero, elevation.raised]}
    >
      <Text style={styles.greeting}>{greeting()}</Text>
      <Text style={styles.date}>{friendlyDate()}</Text>

      <View style={styles.row}>
        {showStreak ? (
          <View style={styles.streakPill}>
            <Ionicons name="flame" size={15} color={color.streak} />
            <Text style={styles.streakText}>
              {streak} {streak === 1 ? 'día seguido' : 'días seguidos'}
            </Text>
          </View>
        ) : (
          <View style={styles.streakPill}>
            <Ionicons name="flame-outline" size={15} color={color.accentInk} />
            <Text style={styles.streakText}>
              {hasPlanToday ? 'Empiezas tu racha hoy' : 'Optimiza hoy para empezar tu racha'}
            </Text>
          </View>
        )}
      </View>

      {totalMin > 0 ? (
        <View style={styles.progressBlock}>
          <View style={styles.progressTrack}>
            <View style={[styles.progressFill, { width: `${Math.round(pct * 100)}%` }]} />
          </View>
          <Text style={styles.progressLabel}>
            {formatDurationMin(doneMin)} de {formatDurationMin(totalMin)} planificados hoy
          </Text>
        </View>
      ) : null}
    </LinearGradient>
  );
}
