import { Ionicons } from '@expo/vector-icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import React, { useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { planningApi } from '../../api/endpoints';
import type { DayPlan, PlanBlock } from '../../api/types';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { ExplanationModal } from '../../components/ExplanationModal';
import { Hero } from '../../components/Hero';
import { QuickAddTaskModal } from '../../components/QuickAddTaskModal';
import { Screen } from '../../components/Screen';
import { radius, spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import { formatDurationMin, nowHHMM, todayIsoDate, wallClockTime } from '../../utils/date';

const TODAY = todayIsoDate();

export default function MiDiaScreen() {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        content: { padding: spacing.lg, paddingBottom: spacing.xxl },
        nowCard: { backgroundColor: color.accentSoft, borderColor: color.accentSoft, marginBottom: spacing.md },
        nowHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.xs },
        nowIconCircle: {
          width: 22,
          height: 22,
          borderRadius: radius.pill,
          backgroundColor: color.surface,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.xs,
        },
        nowLabel: { ...type.caption, color: color.accent, textTransform: 'uppercase' },
        nowMessage: { ...type.bodyStrong, color: color.ink },
        actionRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
        error: { color: color.danger, ...type.body, marginBottom: spacing.md },
        card: { marginBottom: spacing.sm },
        conflictCard: { backgroundColor: color.warnSoft, borderColor: color.warnSoft },
        conflictMessage: { ...type.bodyStrong, color: color.warn },
        conflictSuggestion: { ...type.body, color: color.warn, marginTop: spacing.xs },
        muted: { ...type.body, color: color.muted },
        iconRow: { flexDirection: 'row', alignItems: 'flex-start' },
        iconRowIcon: { marginRight: spacing.sm, marginTop: 2 },
        emptyState: { alignItems: 'center', paddingVertical: spacing.md },
        emptyIconCircle: {
          width: 48,
          height: 48,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: spacing.sm,
        },
        sectionTitle: { ...type.h2, color: color.ink, marginTop: spacing.lg, marginBottom: spacing.sm },
        unplacedSection: { marginTop: spacing.sm },
        unplacedCard: { backgroundColor: color.surfaceAlt },
        unplacedTitle: { ...type.bodyStrong, color: color.ink, marginBottom: spacing.xs },
        suggestion: { ...type.caption, color: color.accent, marginTop: spacing.xs },
      }),
    [color]
  );
  const queryClient = useQueryClient();
  const [optimizing, setOptimizing] = useState(false);
  const [optimizeError, setOptimizeError] = useState<string | null>(null);
  const [addTaskVisible, setAddTaskVisible] = useState(false);
  const [openBlockId, setOpenBlockId] = useState<string | null>(null);
  const [nowMessage, setNowMessage] = useState<string | null>(null);
  const [nowLoading, setNowLoading] = useState(false);

  const planQuery = useQuery<DayPlan | null>({
    queryKey: ['day-plan', TODAY],
    queryFn: async () => {
      try {
        return await planningApi.getDay(TODAY);
      } catch (err: any) {
        if (err?.response?.status === 404) return null;
        throw err;
      }
    },
  });

  const streakQuery = useQuery({
    queryKey: ['streak'],
    queryFn: () => planningApi.streak(),
  });

  const runOptimize = async () => {
    setOptimizeError(null);
    setOptimizing(true);
    try {
      const plan = await planningApi.optimize(TODAY);
      queryClient.setQueryData(['day-plan', TODAY], plan);
      queryClient.invalidateQueries({ queryKey: ['streak'] });
    } catch (err) {
      setOptimizeError(apiErrorMessage(err, 'No pudimos optimizar tu día.'));
    } finally {
      setOptimizing(false);
    }
  };

  const askWhatsNext = async () => {
    setNowLoading(true);
    setNowMessage(null);
    try {
      const res = await planningApi.now();
      setNowMessage(res.message);
    } catch (err) {
      setNowMessage(apiErrorMessage(err));
    } finally {
      setNowLoading(false);
    }
  };

  const plan = planQuery.data;
  const blocks = [...(plan?.blocks ?? [])].sort((a, b) => a.start.localeCompare(b.start));

  return (
    <Screen scroll={false} style={{ padding: 0 }}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={planQuery.isFetching} onRefresh={() => planQuery.refetch()} />}
      >
        <Hero blocks={blocks} streak={streakQuery.data?.current_streak} hasPlanToday={streakQuery.data?.has_plan_today ?? false} />

        <Pressable onPress={askWhatsNext} disabled={nowLoading}>
          <Card style={styles.nowCard}>
            <View style={styles.nowHeader}>
              <View style={styles.nowIconCircle}>
                <Ionicons name="sparkles" size={14} color={color.accent} />
              </View>
              <Text style={styles.nowLabel}>¿Qué hago ahora?</Text>
            </View>
            <Text style={styles.nowMessage}>
              {nowLoading ? 'Pensando…' : nowMessage ?? 'Toca aquí para preguntar'}
            </Text>
          </Card>
        </Pressable>

        <View style={styles.actionRow}>
          <View style={{ flex: 1 }}>
            <Button label={plan ? 'Volver a optimizar mi día' : 'Optimizar mi día'} onPress={runOptimize} loading={optimizing} />
          </View>
          <View style={{ width: spacing.sm }} />
          <Button label="+ Tarea" variant="secondary" onPress={() => setAddTaskVisible(true)} />
        </View>
        {optimizeError ? <Text style={styles.error}>{optimizeError}</Text> : null}

        {plan?.conflicts?.length ? (
          <Card style={[styles.card, styles.conflictCard]}>
            {plan.conflicts.map((c, i) => (
              <View key={i} style={styles.iconRow}>
                <Ionicons name="warning" size={16} color={color.warn} style={styles.iconRowIcon} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.conflictMessage}>{c.message}</Text>
                  <Text style={styles.conflictSuggestion}>{c.suggestion}</Text>
                </View>
              </View>
            ))}
          </Card>
        ) : null}

        {planQuery.isLoading ? (
          <Text style={styles.muted}>Cargando…</Text>
        ) : blocks.length === 0 ? (
          <Card style={styles.card}>
            <View style={styles.emptyState}>
              <View style={styles.emptyIconCircle}>
                <Ionicons name={plan ? 'checkmark-circle-outline' : 'flash-outline'} size={26} color={color.accent} />
              </View>
              <Text style={styles.muted}>
                {plan ? 'No hay nada planificado hoy todavía.' : 'Todavía no has optimizado tu día. Toca el botón de arriba.'}
              </Text>
            </View>
          </Card>
        ) : (
          blocks.map((block) => <BlockRow key={block.id} block={block} onPress={() => setOpenBlockId(block.id)} />)
        )}

        {plan?.unplaced?.length ? (
          <View style={styles.unplacedSection}>
            <Text style={styles.sectionTitle}>Sin ubicar hoy</Text>
            {plan.unplaced.map((u) => (
              <Card key={u.task_id} style={[styles.card, styles.unplacedCard]}>
                <View style={styles.iconRow}>
                  <Ionicons name="alert-circle" size={16} color={color.risk} style={styles.iconRowIcon} />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.unplacedTitle}>{u.title}</Text>
                    <Text style={styles.muted}>{u.reason}</Text>
                    <Text style={styles.suggestion}>{u.suggestion}</Text>
                  </View>
                </View>
              </Card>
            ))}
          </View>
        ) : null}
      </ScrollView>

      <ExplanationModal blockId={openBlockId} onClose={() => setOpenBlockId(null)} />
      <QuickAddTaskModal
        visible={addTaskVisible}
        onClose={() => setAddTaskVisible(false)}
        onCreated={() => {
          setAddTaskVisible(false);
          queryClient.invalidateQueries({ queryKey: ['day-plan', TODAY] });
        }}
      />
    </Screen>
  );
}

function BlockRow({ block, onPress }: { block: PlanBlock; onPress: () => void }) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        card: { marginBottom: spacing.sm },
        pastCard: { opacity: 0.55 },
        blockRow: { flexDirection: 'row', alignItems: 'center' },
        timeCol: { width: 64 },
        time: { ...type.bodyStrong, color: color.ink },
        duration: { ...type.caption, color: color.muted },
        blockIconCircle: {
          width: 28,
          height: 28,
          borderRadius: radius.pill,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        taskIconCircle: { backgroundColor: color.accentSoft },
        eventIconCircle: { backgroundColor: color.surfaceAlt },
        blockBody: { flex: 1, borderLeftWidth: 2, borderLeftColor: color.accentSoft, paddingLeft: spacing.md },
        blockTitle: { ...type.bodyStrong, color: color.ink },
        blockMeta: { ...type.caption, color: color.muted, marginTop: 2 },
      }),
    [color]
  );
  const isTask = block.source_type === 'task';
  const isPast = wallClockTime(block.end) <= nowHHMM();
  return (
    <Pressable onPress={isTask ? onPress : undefined}>
      <Card style={[styles.card, isPast && styles.pastCard]}>
        <View style={styles.blockRow}>
          <View style={styles.timeCol}>
            <Text style={styles.time}>{wallClockTime(block.start)}</Text>
            <Text style={styles.duration}>
              {formatDurationMin(
                (new Date(block.end).getTime() - new Date(block.start).getTime()) / 60000 || 0
              )}
            </Text>
          </View>
          <View style={[styles.blockIconCircle, isTask ? styles.taskIconCircle : styles.eventIconCircle]}>
            <Ionicons
              name={isTask ? 'checkmark' : 'calendar'}
              size={14}
              color={isTask ? color.accent : color.muted}
            />
          </View>
          <View style={styles.blockBody}>
            <Text style={styles.blockTitle}>{block.title}</Text>
            <Text style={styles.blockMeta}>{isTask ? 'Toca para ver por qué' : 'Evento fijo'}</Text>
          </View>
        </View>
      </Card>
    </Pressable>
  );
}
