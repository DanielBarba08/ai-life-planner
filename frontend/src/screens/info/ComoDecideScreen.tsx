import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { useQuery } from '@tanstack/react-query';
import React from 'react';
import { ActivityIndicator, Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { explanationsApi } from '../../api/endpoints';
import type { GeneralEvidenceRead } from '../../api/types';
import { BackHeader } from '../../components/BackHeader';
import { Card } from '../../components/Card';
import { Pill } from '../../components/Pill';
import { Screen } from '../../components/Screen';
import { useTheme } from '../../theme/ThemeContext';
import { radius, spacing, type } from '../../theme/tokens';
import type { AjustesStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AjustesStackParamList, 'ComoDecide'>;

const TOPIC_LABEL: Record<string, string> = {
  descanso: 'Por qué siempre deja un descanso entre bloques',
  sueno: 'Por qué nunca toca tu horario de sueño',
  priorizacion: 'Por qué no ordena solo por fecha límite',
};
const TOPIC_ICON: Record<string, keyof typeof Ionicons.glyphMap> = {
  descanso: 'cafe-outline',
  sueno: 'moon-outline',
  priorizacion: 'swap-vertical-outline',
};

/**
 * "Cómo decide tus horarios" (Ajustes) — evidencia científica real detrás
 * de reglas GENERALES del motor, no de un bloque en particular (ese es el
 * panel "¿Por qué?" de cada bloque, ExplanationModal). Antes no existía
 * ningún lugar honesto donde mostrar esto — ver backend/README.md,
 * sección del Evidence Engine, y app/planning/evidence.py::list_general_evidence.
 */
export default function ComoDecideScreen({ navigation }: Props) {
  const { color, evidenceLevelColor } = useTheme();
  const query = useQuery<GeneralEvidenceRead[]>({ queryKey: ['general-evidence'], queryFn: () => explanationsApi.general() });

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        subtitle: { ...type.body, color: color.muted, marginBottom: spacing.lg },
        card: { marginBottom: spacing.md },
        headerRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
        iconCircle: {
          width: 28,
          height: 28,
          borderRadius: radius.pill,
          backgroundColor: color.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
          marginRight: spacing.sm,
        },
        ruleTitle: { ...type.bodyStrong, color: color.ink, flex: 1 },
        rule: { ...type.body, color: color.ink, lineHeight: 21, marginBottom: spacing.md },
        evidenceBlock: { paddingTop: spacing.md, borderTopWidth: 1, borderTopColor: color.line },
        evidenceHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
        evidenceLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase', marginLeft: spacing.xs, marginRight: spacing.sm, flex: 1 },
        claim: { ...type.body, color: color.ink, lineHeight: 20 },
        citation: { ...type.caption, color: color.muted, marginTop: spacing.sm, fontStyle: 'italic' },
        limitations: { ...type.caption, color: color.muted, marginTop: spacing.xs },
        linkRow: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.sm },
        link: { ...type.caption, color: color.accent, marginLeft: spacing.xs, textDecorationLine: 'underline' },
      }),
    [color]
  );

  return (
    <Screen>
      <BackHeader title="Cómo decide tus horarios" onBack={() => navigation.goBack()} />
      <Text style={styles.subtitle}>
        Reglas que aplican siempre, sin importar el día — con la evidencia científica real detrás de cada una,
        igual de honesta que el panel "¿Por qué?" de cada bloque.
      </Text>

      {query.isLoading ? (
        <ActivityIndicator color={color.accent} />
      ) : (
        (query.data ?? []).map((row) => (
          <Card key={row.topic} style={styles.card}>
            <View style={styles.headerRow}>
              <View style={styles.iconCircle}>
                <Ionicons name={TOPIC_ICON[row.topic] ?? 'flask-outline'} size={15} color={color.accent} />
              </View>
              <Text style={styles.ruleTitle}>{TOPIC_LABEL[row.topic] ?? row.topic}</Text>
            </View>
            <Text style={styles.rule}>{row.system_rule}</Text>

            <View style={styles.evidenceBlock}>
              <View style={styles.evidenceHeader}>
                <Ionicons name="flask-outline" size={13} color={color.muted} />
                <Text style={styles.evidenceLabel}>Evidencia científica</Text>
                <Pill
                  label={row.evidence.evidence_level}
                  fg={evidenceLevelColor[row.evidence.evidence_level].fg}
                  bg={evidenceLevelColor[row.evidence.evidence_level].bg}
                />
              </View>
              <Text style={styles.claim}>{row.evidence.claim}</Text>
              <Text style={styles.citation}>
                {row.evidence.authors} ({row.evidence.year}). {row.evidence.source}.
              </Text>
              <Text style={styles.limitations}>Límites: {row.evidence.limitations}</Text>
              {row.evidence.doi ? (
                <Pressable onPress={() => Linking.openURL(`https://doi.org/${row.evidence.doi}`)} style={styles.linkRow}>
                  <Ionicons name="open-outline" size={13} color={color.accent} />
                  <Text style={styles.link}>Ver fuente original (doi.org/{row.evidence.doi})</Text>
                </Pressable>
              ) : null}
            </View>
          </Card>
        ))
      )}
    </Screen>
  );
}
