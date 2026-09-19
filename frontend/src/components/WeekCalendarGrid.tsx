import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import type { PlanBlock, WeekDay } from '../api/types';
import { ColorTokens, radius, spacing, type } from '../theme/tokens';
import { useTheme } from '../theme/ThemeContext';
import { shortWeekdayLabel, wallClockTime } from '../utils/date';

const HOUR_PX = 56;
const DAY_COL_WIDTH = 112;
const HOUR_AXIS_WIDTH = 40;
const HEADER_HEIGHT = 40;
const MIN_BLOCK_PX = 20;

function hhmmToMinutes(hhmm: string): number {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
}

/**
 * Mismos 3 tipos recurrentes que agregamos a AvailabilityType (ver
 * backend/app/models/availability.py) — se identifican por el prefijo del
 * título que arma app/planning/service.py::_build_fixed_items
 * (f"{tipo.capitalize()} (recurrente)"), porque PlanBlock no trae el tipo
 * de disponibilidad, solo source_type ("event" | "task"). Sirve para
 * pintar comida/aseo/descanso distinto del resto de bloques fijos, que es
 * justo lo que Daniel pidió poder ver de un vistazo en el calendario.
 */
type BlockKind = 'meal' | 'hygiene' | 'rest' | 'task' | 'event';

function classifyBlock(b: PlanBlock): BlockKind {
  if (b.title.startsWith('Comida')) return 'meal';
  if (b.title.startsWith('Aseo')) return 'hygiene';
  if (b.title.startsWith('Descanso')) return 'rest';
  return b.source_type === 'task' ? 'task' : 'event';
}

function kindStyle(kind: BlockKind, color: ColorTokens): { bg: string; fg: string; border: string } {
  switch (kind) {
    case 'meal':
      return { bg: color.goodSoft, fg: color.good, border: color.good };
    case 'hygiene':
      return { bg: color.warnSoft, fg: color.warn, border: color.warn };
    case 'rest':
      return { bg: color.streakSoft, fg: color.streak, border: color.streak };
    case 'task':
      return { bg: color.accentSoft, fg: color.accentDark, border: color.accent };
    default:
      return { bg: color.surfaceAlt, fg: color.muted, border: color.line };
  }
}

/**
 * Vista de calendario de "Mi semana" (pedida por Daniel: "una forma de
 * calendario con todas las actividades que agregue") — alternativa visual
 * a la lista de MiSemanaScreen, misma data (GET /v1/planning/week), sin
 * pegarle una llamada nueva a la API. El eje de horas no se desplaza
 * horizontalmente (solo los 7 días, en un ScrollView horizontal aparte),
 * para poder ubicar la hora de un bloque sin perder de vista la columna.
 */
export function WeekCalendarGrid({ days, todayIso }: { days: WeekDay[]; todayIso: string }) {
  const { color } = useTheme();

  const { rangeStartMin, rangeEndMin } = React.useMemo(() => {
    let min = 7 * 60;
    let max = 23 * 60;
    let any = false;
    for (const day of days) {
      for (const b of day.blocks) {
        const s = hhmmToMinutes(wallClockTime(b.start));
        const e = hhmmToMinutes(wallClockTime(b.end));
        if (!any) {
          min = s;
          max = e;
          any = true;
        } else {
          min = Math.min(min, s);
          max = Math.max(max, e);
        }
      }
    }
    // Colchón de media hora a cada lado y redondeado a la hora, para que
    // ningún bloque quede pegado al borde del grid.
    const start = Math.max(0, Math.floor((min - 30) / 60) * 60);
    const end = Math.min(24 * 60, Math.ceil((max + 30) / 60) * 60);
    return { rangeStartMin: start, rangeEndMin: end };
  }, [days]);

  const hours = React.useMemo(() => {
    const list: number[] = [];
    for (let h = Math.floor(rangeStartMin / 60); h <= Math.ceil(rangeEndMin / 60); h++) list.push(h);
    return list;
  }, [rangeStartMin, rangeEndMin]);

  const gridHeight = ((rangeEndMin - rangeStartMin) / 60) * HOUR_PX;

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        row: { flexDirection: 'row' },
        axisCol: { width: HOUR_AXIS_WIDTH },
        axisSpacer: { height: HEADER_HEIGHT },
        axisHour: { height: HOUR_PX },
        axisHourLabel: { ...type.caption, color: color.muted, marginTop: -6 },
        dayCol: { width: DAY_COL_WIDTH, borderLeftWidth: 1, borderLeftColor: color.line },
        dayHeader: { height: HEADER_HEIGHT, alignItems: 'center', justifyContent: 'center' },
        dayHeaderLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase' },
        dayHeaderLabelToday: { color: color.accent },
        gridArea: { position: 'relative' },
        hourLine: { position: 'absolute', left: 0, right: 0, height: 1, backgroundColor: color.line },
        nowLine: { position: 'absolute', left: 0, right: 0, height: 2, backgroundColor: color.accent },
        block: {
          position: 'absolute',
          left: 2,
          right: 2,
          borderRadius: radius.sm,
          borderLeftWidth: 3,
          paddingHorizontal: 5,
          paddingVertical: 2,
          overflow: 'hidden',
        },
        blockTitle: { ...type.caption, fontSize: 11 },
        blockTime: { ...type.caption, fontSize: 10, opacity: 0.8 },
      }),
    [color]
  );

  const nowMin = React.useMemo(() => {
    const d = new Date();
    return d.getHours() * 60 + d.getMinutes();
  }, []);

  return (
    // Sin ScrollView vertical propio a propósito: Screen (ver
    // components/Screen.tsx) ya envuelve toda la pantalla en uno — anidar
    // dos verticales aquí encima rompe el gesto de scroll en RN. Solo el
    // scroll horizontal de los días es local a este componente.
    <View>
      <View style={styles.row}>
        <View style={styles.axisCol}>
          <View style={styles.axisSpacer} />
          {hours.map((h) => (
            <View key={h} style={styles.axisHour}>
              <Text style={styles.axisHourLabel}>{String(h % 24).padStart(2, '0')}:00</Text>
            </View>
          ))}
        </View>

        {/* Altura explícita: un ScrollView horizontal sin ella colapsa a 0
        de alto en React Native — no hereda el alto de sus hijos como un
        View normal. */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: HEADER_HEIGHT + gridHeight }}>
          <View style={styles.row}>
            {days.map((day) => {
              const isToday = day.date === todayIso;
              return (
                <View key={day.date} style={styles.dayCol}>
                  <View style={styles.dayHeader}>
                    <Text style={[styles.dayHeaderLabel, isToday && styles.dayHeaderLabelToday]}>
                      {shortWeekdayLabel(day.date)}
                    </Text>
                  </View>
                  <View style={[styles.gridArea, { height: gridHeight }]}>
                    {hours.map((h) => (
                      <View key={h} style={[styles.hourLine, { top: (h * 60 - rangeStartMin) * (HOUR_PX / 60) }]} />
                    ))}
                    {isToday && nowMin >= rangeStartMin && nowMin <= rangeEndMin ? (
                      <View style={[styles.nowLine, { top: (nowMin - rangeStartMin) * (HOUR_PX / 60) }]} />
                    ) : null}
                    {day.blocks.map((b) => {
                      const s = hhmmToMinutes(wallClockTime(b.start));
                      const e = hhmmToMinutes(wallClockTime(b.end));
                      const top = Math.max(0, s - rangeStartMin) * (HOUR_PX / 60);
                      const height = Math.max(MIN_BLOCK_PX, (e - s) * (HOUR_PX / 60) - 2);
                      const kind = classifyBlock(b);
                      const kstyle = kindStyle(kind, color);
                      return (
                        <View
                          key={b.id}
                          style={[
                            styles.block,
                            { top, height, backgroundColor: kstyle.bg, borderLeftColor: kstyle.border },
                          ]}
                        >
                          <Text style={[styles.blockTitle, { color: kstyle.fg }]} numberOfLines={height > 34 ? 2 : 1}>
                            {b.title}
                          </Text>
                          {height > 34 ? (
                            <Text style={[styles.blockTime, { color: kstyle.fg }]}>{wallClockTime(b.start)}</Text>
                          ) : null}
                        </View>
                      );
                    })}
                  </View>
                </View>
              );
            })}
          </View>
        </ScrollView>
      </View>
    </View>
  );
}
