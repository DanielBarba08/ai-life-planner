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

type Props = NativeStackScreenProps<AuthStackParamList, 'Login'>;

export default function LoginScreen({ navigation }: Props) {
  const { login } = useAuth();
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
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(apiErrorMessage(err, 'No pudimos iniciar sesión.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <View style={styles.header}>
        <BrandMark />
        <Text style={styles.eyebrow}>AI Life Planner</Text>
        <Text style={styles.title}>Bienvenido de vuelta</Text>
        <Text style={styles.subtitle}>No necesitas hacer más. Necesitas decidir mejor qué hacer con tu tiempo.</Text>
      </View>

      <TextField
        label="Correo"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoComplete="email"
        placeholder="tu@correo.com"
      />
      <TextField
        label="Contraseña"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete="password"
        placeholder="••••••••"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Button label="Entrar" onPress={onSubmit} loading={loading} disabled={!email || !password} />

      <Pressable style={styles.footer} onPress={() => navigation.navigate('Register')}>
        <Text style={styles.footerText}>
          ¿No tienes cuenta? <Text style={styles.footerLink}>Regístrate</Text>
        </Text>
      </Pressable>
    </Screen>
  );
}
