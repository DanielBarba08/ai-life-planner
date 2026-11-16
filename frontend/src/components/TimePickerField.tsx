import { Ionicons } from '@expo/vector-icons';
import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Modal,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';
import { from12Hour, Period, to12Hour } from '../utils/date';

const ITEM_HEIGHT = 40;
const VISIBLE_ITEMS = 5; // impar: la fila de en medio es la seleccionada
const WHEEL_HEIGHT = ITEM_HEIGHT * VISIBLE_ITEMS;
const PADDING = (WHEEL_HEIGHT - ITEM_HEIGHT) / 2;

const HOURS_12 = Array.from({ length: 12 }, (_, i) => String(i + 1)); // "1".."12"
const MINUTES = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0')); // "00".."59"
const PERIODS: Period[] = ['a.m.', 'p.m.'];

/**
 * Selector de hora tipo "rueda" nativa (pedido por Daniel el 17 nov, con
 * una captura del selector de hora de iOS como referencia): tres columnas
 * que se deslizan — hora, minuto y a.m./p.m. — nunca un campo de texto
 * donde teclear la hora, ni siquiera como opción secundaria. Usado en
 * Eventos fijos y Disponibilidad (ver EventFormModal.tsx y
 * AvailabilityFormModal.tsx); Tareas sigue con TimeOptionsField (pills
 * con horas sugeridas) porque ahí no se pidió este cambio.
 *
 * Internamente trabaja en 12 horas (como el selector de referencia), pero
 * sigue guardando y devolviendo "HH:MM" en 24 horas — el mismo formato
 * que ya usa el resto de la app (ver combineDateTime/splitDateTime) — la
 * conversión vive en to12Hour/from12Hour (utils/date.ts), así que nada
 * fuera de este componente necesitó cambiar.
 */
export function TimePickerField({
  label,
  value,
  onChange,
  placeholder = 'Elegir hora',
}: {
  label: string;
  /** Hora "HH:MM" en 24h, o '' si no hay ninguna elegida. */
  value: string;
  onChange: (hhmm: string) => void;
  placeholder?: string;
}) {
  const { color, elevation } = useTheme();
  const [open, setOpen] = useState(false);

  // Estado de trabajo de la rueda mientras el modal está abierto — "Listo"
  // lo aplica con onChange; "Cancelar" lo descarta. Si no hay valor
  // todavía, arranca en 12:00 p.m. en vez de inventar una hora cualquiera
  // (mediodía es el punto neutral más razonable para empezar a elegir).
  const [hour12, setHour12] = useState(12);
  const [minute, setMinute] = useState(0);
  const [period, setPeriod] = useState<Period>('p.m.');

  const openPicker = () => {
    const base = value ? to12Hour(value) : { hour12: 12, minute: 0, period: 'p.m.' as Period };
    setHour12(base.hour12);
    setMinute(base.minute);
    setPeriod(base.period);
    setOpen(true);
  };

  const confirm = () => {
    onChange(from12Hour(hour12, minute, period));
    setOpen(false);
  };

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
          width: 280,
          maxWidth: '90%',
          backgroundColor: color.surface,
          borderRadius: radius.lg,
          padding: spacing.lg,
          ...elevation.raised,
        },
        headerLabel: { ...type.h2, color: color.ink, marginBottom: spacing.md, textAlign: 'center' },
        wheelRow: { flexDirection: 'row', justifyContent: 'center', height: WHEEL_HEIGHT },
        centerHighlight: {
          position: 'absolute',
          left: 0,
          right: 0,
          top: PADDING,
          height: ITEM_HEIGHT,
          borderRadius: radius.md,
          backgroundColor: color.surfaceAlt,
        },
        footer: {
          flexDirection: 'row',
          justifyContent: 'space-between',
          marginTop: spacing.md,
          paddingTop: spacing.md,
          borderTopWidth: 1,
          borderTopColor: color.line,
        },
        footerLabel: { ...type.bodyStrong, color: color.accent },
        footerLabelMuted: { ...type.bodyStrong, color: color.muted },
      }),
    [color, elevation, value]
  );

  return (
    <View style={styles.wrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <Pressable style={styles.field} onPress={openPicker}>
        <Ionicons name="time-outline" size={16} color={color.muted} style={{ marginRight: spacing.sm }} />
        <Text style={styles.fieldText}>{value || placeholder}</Text>
      </Pressable>

      <Modal visible={open} animationType="fade" transparent onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          <Pressable style={styles.card} onPress={() => {}}>
            <Text style={styles.headerLabel}>{label}</Text>

            {/* Se vuelve a montar cada vez que se abre (nunca se renderiza
                mientras open=false) para que cada rueda arranque en la
                posición correcta vía su `contentOffset` inicial — un
                <Modal> de React Native no desmonta su contenido solo por
                cambiar `visible`. */}
            {open ? (
              <View style={styles.wheelRow}>
                <View pointerEvents="none" style={styles.centerHighlight} />
                <WheelColumn items={HOURS_12} selectedIndex={hour12 - 1} onSelect={(i) => setHour12(i + 1)} width={52} />
                <WheelColumn items={MINUTES} selectedIndex={minute} onSelect={setMinute} width={52} />
                <WheelColumn
                  items={PERIODS}
                  selectedIndex={PERIODS.indexOf(period)}
                  onSelect={(i) => setPeriod(PERIODS[i])}
                  width={64}
                />
              </View>
            ) : null}

            <View style={styles.footer}>
              <Pressable onPress={() => setOpen(false)} hitSlop={8}>
                <Text style={styles.footerLabelMuted}>Cancelar</Text>
              </Pressable>
              <Pressable onPress={confirm} hitSlop={8}>
                <Text style={styles.footerLabel}>Listo</Text>
              </Pressable>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

/**
 * Una columna deslizable del selector — implementada a mano con
 * ScrollView + snapToInterval en vez de una librería nativa de "wheel
 * picker": esta app corre tanto en iOS/Android como en la build web
 * (Cloudflare Pages, ver frontend/README.md), y una librería nativa no
 * funcionaría ahí. El fade de los números que se alejan del centro usa
 * Animated sin useNativeDriver (contentOffset no es animable de forma
 * nativa en web), y el "asentado" final se detecta dos veces por
 * seguridad: con onMomentumScrollEnd (nativo) y con un debounce sobre
 * onScroll (necesario en la versión web, donde un scroll con la rueda del
 * mouse no siempre dispara el evento de momentum).
 */
function WheelColumn({
  items,
  selectedIndex,
  onSelect,
  width,
}: {
  items: string[];
  selectedIndex: number;
  onSelect: (index: number) => void;
  width: number;
}) {
  const { color } = useTheme();
  const scrollRef = useRef<any>(null);
  const scrollY = useRef(new Animated.Value(selectedIndex * ITEM_HEIGHT)).current;
  const settleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (settleTimer.current) clearTimeout(settleTimer.current);
  }, []);

  const finalizeFromOffset = (y: number) => {
    if (settleTimer.current) {
      clearTimeout(settleTimer.current);
      settleTimer.current = null;
    }
    const index = Math.max(0, Math.min(items.length - 1, Math.round(y / ITEM_HEIGHT)));
    scrollRef.current?.scrollTo?.({ y: index * ITEM_HEIGHT, animated: true });
    onSelect(index);
  };

  const handleScroll = Animated.event([{ nativeEvent: { contentOffset: { y: scrollY } } }], {
    useNativeDriver: false,
    listener: (e: NativeSyntheticEvent<NativeScrollEvent>) => {
      const y = e.nativeEvent.contentOffset.y;
      if (settleTimer.current) clearTimeout(settleTimer.current);
      settleTimer.current = setTimeout(() => finalizeFromOffset(y), 160);
    },
  });

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        col: { width, height: WHEEL_HEIGHT },
        item: { height: ITEM_HEIGHT, alignItems: 'center', justifyContent: 'center' },
        itemText: { ...type.h2, fontSize: 19, color: color.ink },
      }),
    [color, width]
  );

  return (
    <View style={styles.col}>
      <Animated.ScrollView
        ref={scrollRef}
        showsVerticalScrollIndicator={false}
        snapToInterval={ITEM_HEIGHT}
        decelerationRate="fast"
        contentContainerStyle={{ paddingVertical: PADDING }}
        contentOffset={{ x: 0, y: selectedIndex * ITEM_HEIGHT }}
        onScroll={handleScroll}
        scrollEventThrottle={16}
        onMomentumScrollEnd={(e) => finalizeFromOffset(e.nativeEvent.contentOffset.y)}
      >
        {items.map((label, i) => {
          const inputRange = [
            (i - 2) * ITEM_HEIGHT,
            (i - 1) * ITEM_HEIGHT,
            i * ITEM_HEIGHT,
            (i + 1) * ITEM_HEIGHT,
            (i + 2) * ITEM_HEIGHT,
          ];
          const opacity = scrollY.interpolate({
            inputRange,
            outputRange: [0.2, 0.45, 1, 0.45, 0.2],
            extrapolate: 'clamp',
          });
          return (
            <View key={`${label}-${i}`} style={styles.item}>
              <Animated.Text style={[styles.itemText, { opacity }]}>{label}</Animated.Text>
            </View>
          );
        })}
      </Animated.ScrollView>
    </View>
  );
}
