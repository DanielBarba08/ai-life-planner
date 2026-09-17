import React from 'react';
import { StyleSheet, Text, TextInput, TextInputProps, View } from 'react-native';

import { useTheme } from '../theme/ThemeContext';
import { radius, spacing, type } from '../theme/tokens';

interface TextFieldProps extends TextInputProps {
  label: string;
  error?: string | null;
}

export function TextField({ label, error, style, ...rest }: TextFieldProps) {
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        wrap: { marginBottom: spacing.md },
        label: { ...type.caption, color: color.muted, marginBottom: spacing.xs, textTransform: 'uppercase' },
        input: {
          borderWidth: 1,
          borderColor: color.line,
          borderRadius: radius.md,
          paddingHorizontal: spacing.md,
          paddingVertical: 12,
          fontSize: 16,
          color: color.ink,
          backgroundColor: color.surface,
        },
        inputError: { borderColor: color.danger },
        error: { color: color.danger, ...type.caption, marginTop: spacing.xs },
      }),
    [color]
  );

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, error ? styles.inputError : null, style]}
        placeholderTextColor={color.muted}
        autoCapitalize="none"
        {...rest}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}
