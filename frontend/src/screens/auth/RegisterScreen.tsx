import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { apiErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { BrandMark } from '../../components/BrandMark';
import { Button } from '../../components/Button';
import { Screen } from '../../components/Screen';
import { TextField } from '../../components/TextField';
import { spacing, type } from '../../theme/tokens';
import { useTheme } from '../../theme/ThemeContext';
import type { AuthStackParamList } from '../../navigation/types';

type Props = NativeStackScreenProps<AuthStackParamList, 'Register'>;

export default function RegisterScreen({ navigation }: Props) {
  const { register } = useAuth();
  const { color } = useTheme();
  const styles = React.useMemo(
    () =>
      StyleSheet.create({
        header: { marginBottom: spacing.xl, marginTop: spacing.xl },
        eyebrow: { ...type.caption, color: color.accent, textTransform: 'uppercase', marginBottom: spacing.sm },
        title: { ...type.display, color: color.ink, marginBottom: spacing.sm },
        subtitle: { ...type.body, color: color.muted },
        error: { color: color.danger, marginBottom: spacing.md, ...type.body },
        footer: { marginTop: spacing.lg, alignItems: 'center' },
        footerText: { ...type.body, color: color.muted },
        footerLink: { ...type.bodyStrong, color: color.accent },
      }),
    [color]
  );
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      await register(email.trim(), password, name.trim() || undefined, timezone);
    } catch (err) {
      setError(apiErrorMessage(err, 'No pudimos crear tu cuenta.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <View style={styles.header}>
        <BrandMark />
        <Text style={styles.eyebrow}>AI Life Planner</Text>
        <Text style={styles.title}>Crea tu cuenta</Text>
        <Text style={styles.subtitle}>Te tomará un minuto. Después ajustamos tu horario en unos pasos rápidos.</Text>
      </View>

      <TextField label="Nombre (opcional)" value={name} onChangeText={setName} placeholder="¿Cómo te llamas?" autoCapitalize="words" />
      <TextField
        label="Correo"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoComplete="email"
        placeholder="tu@correo.com"
      />
      <TextField
        label="Contraseña (mínimo 8 caracteres)"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        placeholder="••••••••"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Button
        label="Crear cuenta"
        onPress={onSubmit}
        loading={loading}
        disabled={!email || password.length < 8}
      />

      <Pressable style={styles.footer} onPress={() => navigation.navigate('Login')}>
        <Text style={styles.footerText}>
          ¿Ya tienes cuenta? <Text style={styles.footerLink}>Entra</Text>
        </Text>
      </Pressable>
    </Screen>
  );
}
