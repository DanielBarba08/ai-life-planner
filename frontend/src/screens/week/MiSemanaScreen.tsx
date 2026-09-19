import { Ionicons } from '@expo/vector-icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { planningApi } from '../../api/endpoints';
import type { WeekDay } from '../../api/types';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Pill } from '../../components/Pill';
import { Screen } from '../../components/Screen';
import { WeekCalendarGrid } from '../../components/WeekCalendarGrid';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import { addDaysIso, formatDurationMin, mondayOfWeek, shortWeekdayLabel, todayIsoDate, wallClockTime } from '../../utils/date';

type ViewMode = 'lista' | 'calendario';

const TODAY = todayIsoDate();

/**
 * "Mi semana" conectada de verdad (cerraba el primer hueco de API real que
 * identificamos al construir el frontend — ver backend/README.md). Un solo
 * GET /v1/planning/week/{lunes} trae los 7 días; cada día muestra sus
 * bloques reales si ya se optimizó, o un botón para optimizarlo ahí mismo
 * si no — nunca datos inventados para rellenar un día vacío.
 */
export default function MiSemanaScreen() {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        eyebrow: { ...type.caption, color: color.accent, textTransform: 'uppercase' },
        title: { ...type.display, color: color.ink, marginTop: spacing.xs, marginBottom: spacing.md },
        nav: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
        navBtn: {
          width: 34,
          height: 34,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
        },
        navLabelWrap: { alignItems: 'center' },
        navLabel: { ...type.bodyStrong, color: color.ink },
        navToday: { ...type.caption, color: color.accent, marginTop: 2 },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        muted: { ...type.body, color: color.muted },
        modeRow: { flexDirection: 'row', marginBottom: spacing.md },
        modeWrap: { marginRight: spacing.sm },
      }),
    [color]
  );
  const queryClient = useQueryClient();
  const [weekStart, setWeekStart] = useState(mondayOfWeek(TODAY));
  const [optimizingDate, setOptimizingDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('lista');

  const weekQuery = useQuery<WeekDay[]>({
    queryKey: ['week', weekStart],
    queryFn: () => planningApi.week(weekStart),
  });

  const optimizeDay = async (date: string) => {
    setError(null);
    setOptimizingDate(date);
    try {
      await planningApi.optimize(date);
      await queryClient.invalidateQueries({ queryKey: ['week', weekStart] });
      if (date === TODAY) {
        queryClient.invalidateQueries({ queryKey: ['day-plan', TODAY] });
        queryClient.invalidateQueries({ queryKey: ['streak'] });
      }
    } catch (err) {
      setError(apiErrorMessage(err, 'No pudimos optimizar ese día.'));
    } finally {
      setOptimizingDate(null);
    }
  };

  const weekEnd = addDaysIso(weekStart, 6);
  const isCurrentWeek = weekStart === mondayOfWeek(TODAY);

  return (
    <Screen>
      <Text style={styles.eyebrow}>Esta semana</Text>
      <Text style={styles.title}>Mi semana</Text>

      <View style={styles.nav}>
        <Pressable style={styles.navBtn} onPress={() => setWeekStart(addDaysIso(weekStart, -7))}>
          <Ionicons name="chevron-back" size={18} color={color.accent} />
        </Pressable>
        <View style={styles.navLabelWrap}>
          <Text style={styles.navLabel}>
            {shortWeekdayLabel(weekStart)} – {shortWeekdayLabel(weekEnd)}
          </Text>
          {!isCurrentWeek ? (
            <Pressable onPress={() => setWeekStart(mondayOfWeek(TODAY))}>
              <Text style={styles.navToday}>Ir a esta semana</Text>
            </Pressable>
          ) : null}
        </View>
        <Pressable style={styles.navBtn} onPress={() => setWeekStart(addDaysIso(weekStart, 7))}>
          <Ionicons name="chevron-forward" size={18} color={color.accent} />
        </Pressable>
      </View>

      <View style={styles.modeRow}>
        <Pressable style={styles.modeWrap} onPress={() => setViewMode('lista')}>
          <Pill label="Lista" fg={viewMode === 'lista' ? color.accentInk : color.muted} bg={viewMode === 'lista' ? color.accent : color.surfaceAlt} />
        </Pressable>
        <Pressable style={styles.modeWrap} onPress={() => setViewMode('calendario')}>
          <Pill
            label="Calendario"
            fg={viewMode === 'calendario' ? color.accentInk : color.muted}
            bg={viewMode === 'calendario' ? color.accent : color.surfaceAlt}
          />
        </Pressable>
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {weekQuery.isLoading ? (
        <ActivityIndicator color={color.accent} style={{ marginTop: spacing.xl }} />
      ) : weekQuery.isError ? (
        <Text style={styles.muted}>No pudimos cargar tu semana.</Text>
      ) : viewMode === 'calendario' ? (
        <WeekCalendarGrid days={weekQuery.data ?? []} todayIso={TODAY} />
      ) : (
        (weekQuery.data ?? []).map((day) => (
          <DayCard
            key={day.date}
            day={day}
            isToday={day.date === TODAY}
            optimizing={optimizingDate === day.date}
            onOptimize={() => optimizeDay(day.date)}
          />
        ))
      )}
    </Screen>
  );
}

function DayCard({
  day,
  isToday,
  optimizing,
  onOptimize,
}: {
  day: WeekDay;
  isToday: boolean;
  optimizing: boolean;
  onOptimize: () => void;
}) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        dayCard: { marginBottom: spacing.sm },
        dayCardToday: { borderColor: color.accent, borderWidth: 1.5 },
        dayHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xs },
        dayLabel: { ...type.h2, color: color.ink },
        dayLabelToday: { color: color.accent },
        dayMinutes: { ...type.caption, color: color.muted },
        muted: { ...type.body, color: color.muted },
        emptyRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
        blockRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 4 },
        blockTime: { ...type.caption, color: color.muted, width: 48 },
        blockTitle: { ...type.body, color: color.ink, flex: 1 },
      }),
    [color]
  );
  return (
    <Card style={[styles.dayCard, isToday && styles.dayCardToday]}>
      <View style={styles.dayHeader}>
        <Text style={[styles.dayLabel, isToday && styles.dayLabelToday]}>
          {shortWeekdayLabel(day.date)}
          {isToday ? ' · hoy' : ''}
        </Text>
        {day.has_plan && day.blocks.length > 0 ? (
          <Text style={styles.dayMinutes}>{formatDurationMin(day.total_requested_min)}</Text>
        ) : null}
      </View>

      {!day.has_plan ? (
        <View style={styles.emptyRow}>
          <Text style={styles.muted}>Sin optimizar todavía.</Text>
          <Button label="Optimizar" variant="secondary" onPress={onOptimize} loading={optimizing} />
        </View>
      ) : day.blocks.length === 0 ? (
        <Text style={styles.muted}>Día libre — no hay nada planificado.</Text>
      ) : (
        day.blocks.map((b) => (
          <View key={b.id} style={styles.blockRow}>
            <Text style={styles.blockTime}>{wallClockTime(b.start)}</Text>
            <Text style={styles.blockTitle} numberOfLines={1}>
              {b.title}
            </Text>
          </View>
        ))
      )}
    </Card>
  );
}
