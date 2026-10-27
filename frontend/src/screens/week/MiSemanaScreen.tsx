import { Ionicons } from '@expo/vector-icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { planningApi } from '../../api/endpoints';
import type { PlanBlock, WeekDay } from '../../api/types';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Pill } from '../../components/Pill';
import { Screen } from '../../components/Screen';
import { classifyBlock, kindIcon, kindStyle, WeekCalendarGrid } from '../../components/WeekCalendarGrid';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import {
  addDaysIso,
  dayOfMonth,
  mondayOfWeek,
  nowHHMM,
  shortWeekdayLabel,
  todayIsoDate,
  wallClockTime,
  weekdayAbbr,
} from '../../utils/date';

type ViewMode = 'dia' | 'calendario';

const TODAY = todayIsoDate();

/**
 * "Mi semana" conectada de verdad (cerraba el primer hueco de API real que
 * identificamos al construir el frontend — ver backend/README.md). Un solo
 * GET /v1/planning/week/{lunes} trae los 7 días; cada día muestra sus
 * bloques reales si ya se optimizó, o un botón para optimizarlo ahí mismo
 * si no — nunca datos inventados para rellenar un día vacío.
 *
 * Vista "Día" (pedida por Daniel con una captura de referencia, 27 oct):
 * selector horizontal de los 7 días de la semana + la lista del día
 * seleccionado, con un check lleno en los bloques ya pasados y un círculo
 * vacío en los que faltan — reemplaza la vista "Lista" anterior (7
 * tarjetas apiladas, una por día). "Calendario" (la cuadrícula de horas,
 * ver WeekCalendarGrid.tsx) se queda igual como segunda opción, por si
 * Daniel quiere ver toda la semana de un vistazo.
 */
export default function MiSemanaScreen() {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        eyebrow: { ...type.caption, color: color.accent, textTransform: 'uppercase' },
        title: { ...type.display, color: color.ink, marginTop: spacing.xs, marginBottom: spacing.xs },
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.md },
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
        modeRow: { flexDirection: 'row', marginBottom: spacing.lg },
        modeWrap: { marginRight: spacing.sm },
      }),
    [color]
  );
  const queryClient = useQueryClient();
  const [weekStart, setWeekStartRaw] = useState(mondayOfWeek(TODAY));
  const [selectedDate, setSelectedDate] = useState(TODAY);
  const [optimizingDate, setOptimizingDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('dia');

  // Cambiar de semana mueve el día seleccionado con ella: si la nueva
  // semana es la semana actual, selecciona hoy; si no, su lunes — nunca
  // deja seleccionado un día que ya no pertenece a la semana visible.
  const setWeekStart = (next: string) => {
    setWeekStartRaw(next);
    setSelectedDate(next === mondayOfWeek(TODAY) ? TODAY : next);
  };

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
  const selectedDay = (weekQuery.data ?? []).find((d) => d.date === selectedDate);

  return (
    <Screen>
      <Text style={styles.eyebrow}>Esta semana</Text>
      <Text style={styles.title}>Mi semana</Text>
      <Text style={styles.subtitle}>Tu semana, en equilibrio</Text>

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
        <Pressable style={styles.modeWrap} onPress={() => setViewMode('dia')}>
          <Pill label="Día" fg={viewMode === 'dia' ? color.accentInk : color.muted} bg={viewMode === 'dia' ? color.accent : color.surfaceAlt} />
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
        <>
          <DayStrip
            days={(weekQuery.data ?? []).map((d) => d.date)}
            selectedDate={selectedDate}
            todayIso={TODAY}
            onSelect={setSelectedDate}
          />
          <DayDetail
            day={selectedDay}
            dateIso={selectedDate}
            isToday={selectedDate === TODAY}
            optimizing={optimizingDate === selectedDate}
            onOptimize={() => optimizeDay(selectedDate)}
          />
        </>
      )}
    </Screen>
  );
}

/** Selector horizontal de los 7 días de la semana visible — el elemento
 * central del diseño que pidió Daniel. Siempre pinta los 7 días de
 * `weekStart` (aunque `weekQuery` siga cargando esa semana en particular
 * vendría vacío por un instante; MiSemanaScreen ya cubre ese caso con su
 * propio loading state antes de montar este componente). */
function DayStrip({
  days,
  selectedDate,
  todayIso,
  onSelect,
}: {
  days: string[];
  selectedDate: string;
  todayIso: string;
  onSelect: (date: string) => void;
}) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        strip: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.lg },
        chip: {
          flex: 1,
          marginHorizontal: 2,
          paddingVertical: spacing.sm,
          borderRadius: radius.lg,
          alignItems: 'center',
        },
        chipSelected: { backgroundColor: color.accent },
        abbr: { ...type.caption, color: color.muted, textTransform: 'uppercase' },
        abbrSelected: { color: color.accentInk },
        num: { ...type.bodyStrong, color: color.ink, marginTop: 2 },
        numSelected: { color: color.accentInk },
        todayDot: {
          width: 4,
          height: 4,
          borderRadius: radius.pill,
          backgroundColor: color.accent,
          marginTop: 4,
        },
        todayDotSelected: { backgroundColor: color.accentInk },
      }),
    [color]
  );
  return (
    <View style={styles.strip}>
      {days.map((date) => {
        const isSelected = date === selectedDate;
        const isToday = date === todayIso;
        return (
          <Pressable key={date} style={[styles.chip, isSelected && styles.chipSelected]} onPress={() => onSelect(date)}>
            <Text style={[styles.abbr, isSelected && styles.abbrSelected]}>{weekdayAbbr(date)}</Text>
            <Text style={[styles.num, isSelected && styles.numSelected]}>{dayOfMonth(date)}</Text>
            {isToday ? <View style={[styles.todayDot, isSelected && styles.todayDotSelected]} /> : null}
          </Pressable>
        );
      })}
    </View>
  );
}

function DayDetail({
  day,
  dateIso,
  isToday,
  optimizing,
  onOptimize,
}: {
  day: WeekDay | undefined;
  dateIso: string;
  isToday: boolean;
  optimizing: boolean;
  onOptimize: () => void;
}) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        sectionTitle: { ...type.h1, color: color.ink, marginBottom: spacing.md },
        muted: { ...type.body, color: color.muted },
        emptyCard: { marginBottom: spacing.sm },
        emptyRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
      }),
    [color]
  );

  const label = isToday ? 'Tu día de hoy' : `Tu día: ${shortWeekdayLabel(dateIso)}`;
  const blocks = [...(day?.blocks ?? [])].sort((a, b) => a.start.localeCompare(b.start));

  return (
    <View>
      <Text style={styles.sectionTitle}>{label}</Text>

      {!day || !day.has_plan ? (
        <Card style={styles.emptyCard}>
          <View style={styles.emptyRow}>
            <Text style={styles.muted}>Sin optimizar todavía.</Text>
            <Button label="Optimizar" variant="secondary" onPress={onOptimize} loading={optimizing} />
          </View>
        </Card>
      ) : blocks.length === 0 ? (
        <Card style={styles.emptyCard}>
          <Text style={styles.muted}>Día libre — no hay nada planificado.</Text>
        </Card>
      ) : (
        blocks.map((b) => <DayBlockRow key={b.id} block={b} dateIso={dateIso} />)
      )}
    </View>
  );
}

function DayBlockRow({ block, dateIso }: { block: PlanBlock; dateIso: string }) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        card: { marginBottom: spacing.sm },
        row: { flexDirection: 'row', alignItems: 'center' },
        iconCircle: {
          width: 36,
          height: 36,
          borderRadius: radius.pill,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        body: { flex: 1 },
        title: { ...type.bodyStrong, color: color.ink },
        time: { ...type.caption, color: color.muted, marginTop: 2 },
        doneCircle: {
          width: 24,
          height: 24,
          borderRadius: radius.pill,
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: color.good,
        },
        pendingCircle: {
          width: 24,
          height: 24,
          borderRadius: radius.pill,
          borderWidth: 1.5,
          borderColor: color.line,
        },
      }),
    [color]
  );

  // Un día pasado de la semana cuenta como completo entero; uno futuro,
  // nada; el día de hoy compara bloque por bloque contra la hora actual
  // (mismo criterio que BlockRow en MiDiaScreen.tsx — aquí se muestra como
  // check explícito en vez de opacidad, que es justo el elemento que pidió
  // Daniel en su captura de referencia).
  const done = dateIso < TODAY || (dateIso === TODAY && wallClockTime(block.end) <= nowHHMM());

  const kind = classifyBlock(block);
  const kstyle = kindStyle(kind, color);

  return (
    <Card style={styles.card}>
      <View style={styles.row}>
        <View style={[styles.iconCircle, { backgroundColor: kstyle.bg }]}>
          <Ionicons name={kindIcon(kind)} size={16} color={kstyle.fg} />
        </View>
        <View style={styles.body}>
          <Text style={styles.title}>{block.title}</Text>
          <Text style={styles.time}>
            {wallClockTime(block.start)} – {wallClockTime(block.end)}
          </Text>
        </View>
        {done ? (
          <View style={styles.doneCircle}>
            <Ionicons name="checkmark" size={14} color={color.accentInk} />
          </View>
        ) : (
          <View style={styles.pendingCircle} />
        )}
      </View>
    </Card>
  );
}
