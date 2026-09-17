import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  disabled?: boolean;
  testID?: string;
}

export function Button({ label, onPress, variant = 'primary', loading, disabled, testID }: ButtonProps) {
  const { color, elevation } = useTheme();
  const isDisabled = disabled || loading;

  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        base: {
          paddingVertical: 14,
          paddingHorizontal: spacing.lg,
          borderRadius: radius.md,
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 48,
        },
        primary: { backgroundColor: color.accent, ...elevation.low },
        secondary: { backgroundColor: color.accentSoft },
        ghost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: color.line },
        disabled: { opacity: 0.5 },
        pressed: { opacity: 0.85 },
        label: { ...type.bodyStrong },
      }),
    [color, elevation]
  );

  return (
    <Pressable
      testID={testID}
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.base,
        variant === 'primary' && styles.primary,
        variant === 'secondary' && styles.secondary,
        variant === 'ghost' && styles.ghost,
        isDisabled && styles.disabled,
        pressed && !isDisabled && styles.pressed,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? color.accentInk : color.accent} />
      ) : (
        <Text
          style={[
            styles.label,
            variant === 'primary' && { color: color.accentInk },
            variant !== 'primary' && { color: color.accent },
          ]}
        >
          {label}
        </Text>
      )}
    </Pressable>
  );
}
