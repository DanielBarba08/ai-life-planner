import { Ionicons } from '@expo/vector-icons';
import { useQuery } from '@tanstack/react-query';
import React from 'react';
import { ActivityIndicator, Linking, Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { explanationsApi } from '../api/endpoints';
import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { confidenceColorFor, confidenceLabel, Pill } from './Pill';

/**
 * Panel "¿Por qué?" (sección 12 del brief): separa SIEMPRE, en secciones
 * visualmente distintas, dato del usuario / regla del sistema / evidencia
 * científica / inferencia de IA — nunca los mezcla en un párrafo. Si
 * `evidence` viene null, esa sección completa no se muestra — no se rellena
 * con un placeholder ("sin evidencia disponible" sería casi tan engañoso
 * como inventar una cita, porque implica que se buscó y no se encontró).
 */
export function ExplanationModal({ blockId, onClose }: { blockId: string | null; onClose: () => void }) {
  const { color, elevation, evidenceLevelColor } = useTheme();
  const confidenceColor = confidenceColorFor(color);
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        backdrop: { flex: 1, backgroundColor: 'rgba(20,20,16,0.4)', justifyContent: 'flex-end' },
        sheet: {
          backgroundColor: color.surface,
          borderTopLeftRadius: radius.xl,
          borderTopRightRadius: radius.xl,
          padding: spacing.lg,
          maxHeight: '85%',
          ...elevation.raised,
        },
        handle: { alignSelf: 'center', width: 36, height: 4, borderRadius: 2, backgroundColor: color.line, marginBottom: spacing.md },
        eyebrow: { ...type.caption, color: color.accent, textTransform: 'uppercase' },
        title: { ...type.h1, color: color.ink, marginTop: spacing.xs, marginBottom: spacing.md },
        body: { ...type.body, color: color.ink, lineHeight: 21 },
        evidenceHeader: { marginBottom: spacing.sm },
        citation: { ...type.caption, color: color.muted, marginTop: spacing.sm, fontStyle: 'italic' },
        limitations: { ...type.caption, color: color.muted, marginTop: spacing.xs },
        linkRow: { flexDirection: 'row', alignItems: 'center', marginTop: spacing.sm },
        link: { ...type.caption, color: color.accent, marginLeft: spacing.xs, textDecorationLine: 'underline' },
        confidenceRow: { marginTop: spacing.sm },
        closeBtn: { paddingVertical: spacing.md, alignItems: 'center' },
        closeLabel: { ...type.bodyStrong, color: color.accent },
      }),
    [color, elevation]
  );

  const query = useQuery({
    queryKey: ['explanation', blockId],
    queryFn: () => explanationsApi.get(blockId as string),
    enabled: !!blockId,
  });

  return (
    <Modal visible={!!blockId} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          {query.isLoading ? (
            <ActivityIndicator style={{ marginVertical: spacing.xl }} color={color.accent} />
          ) : query.isError ? (
            <Text style={styles.body}>Este bloque no tiene una explicación asociada (es un evento que agregaste tú).</Text>
          ) : query.data ? (
            <ScrollView showsVerticalScrollIndicator={false}>
              <Text style={styles.eyebrow}>¿Por qué?</Text>
              <Text style={styles.title}>{query.data.block_title}</Text>

              <Section label="Tus datos" icon="person-outline">
                <Text style={styles.body}>{query.data.user_data}</Text>
              </Section>

              <Section label="Regla del sistema" icon="cog-outline">
                <Text style={styles.body}>{query.data.system_rule}</Text>
              </Section>

              {query.data.evidence ? (
                <Section label="Evidencia científica" icon="flask-outline">
                  <View style={styles.evidenceHeader}>
                    <Pill
                      label={query.data.evidence.evidence_level}
                      fg={evidenceLevelColor[query.data.evidence.evidence_level].fg}
                      bg={evidenceLevelColor[query.data.evidence.evidence_level].bg}
                    />
                  </View>
                  <Text style={styles.body}>{query.data.evidence.claim}</Text>
                  <Text style={styles.citation}>
                    {query.data.evidence.authors} ({query.data.evidence.year}). {query.data.evidence.source}.
                  </Text>
                  <Text style={styles.limitations}>Límites: {query.data.evidence.limitations}</Text>
                  {query.data.evidence.doi ? (
                    <Pressable
                      onPress={() => Linking.openURL(`https://doi.org/${query.data!.evidence!.doi}`)}
                      style={styles.linkRow}
                    >
                      <Ionicons name="open-outline" size={13} color={color.accent} />
                      <Text style={styles.link}>Ver fuente original (doi.org/{query.data.evidence.doi})</Text>
                    </Pressable>
                  ) : null}
                </Section>
              ) : null}

              <Section label="Inferencia de IA" icon="sparkles-outline">
                <Text style={styles.body}>{query.data.ai_inference}</Text>
                <View style={styles.confidenceRow}>
                  <Pill
                    label={confidenceLabel[query.data.confidence]}
                    fg={confidenceColor[query.data.confidence].fg}
                    bg={confidenceColor[query.data.confidence].bg}
                  />
                </View>
              </Section>
            </ScrollView>
          ) : null}

          <Pressable style={styles.closeBtn} onPress={onClose}>
            <Text style={styles.closeLabel}>Cerrar</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

function Section({
  label,
  icon,
  children,
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  children: React.ReactNode;
}) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        section: { marginBottom: spacing.lg, paddingBottom: spacing.md, borderBottomWidth: 1, borderBottomColor: color.line },
        sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.xs },
        sectionLabel: { ...type.caption, color: color.muted, textTransform: 'uppercase' },
      }),
    [color]
  );
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Ionicons name={icon} size={14} color={color.muted} style={{ marginRight: spacing.xs }} />
        <Text style={styles.sectionLabel}>{label}</Text>
      </View>
      {children}
    </View>
  );
}
