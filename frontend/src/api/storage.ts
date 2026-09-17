import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * AsyncStorage (no expo-secure-store) a propósito: SecureStore ni siquiera
 * existe en web, y este MVP corre igual en Expo Go / web / nativo. Guardar
 * los tokens sin cifrado adicional en el dispositivo es una limitación
 * conocida — igual que el backend documenta que los refresh tokens no se
 * pueden revocar individualmente (ver backend/README.md) — aceptable para
 * el MVP, documentada para no perderla de vista.
 */

const ACCESS_KEY = 'ailp.access_token';
const REFRESH_KEY = 'ailp.refresh_token';

export async function getTokens() {
  const [access, refresh] = await Promise.all([
    AsyncStorage.getItem(ACCESS_KEY),
    AsyncStorage.getItem(REFRESH_KEY),
  ]);
  return { access, refresh };
}

export async function setTokens(access: string, refresh: string) {
  await Promise.all([AsyncStorage.setItem(ACCESS_KEY, access), AsyncStorage.setItem(REFRESH_KEY, refresh)]);
}

export async function clearTokens() {
  await Promise.all([AsyncStorage.removeItem(ACCESS_KEY), AsyncStorage.removeItem(REFRESH_KEY)]);
}
