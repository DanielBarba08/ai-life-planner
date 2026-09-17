/** "2026-09-14" en la fecha local del dispositivo (nunca toISOString(), que es UTC). */
export function todayIsoDate(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Suma (o resta, con n negativo) días a una fecha ISO "2026-09-14" — en
 * fecha local, nunca con aritmética de milisegundos UTC. */
export function addDaysIso(iso: string, n: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d + n);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

/** Lunes de la semana que contiene `iso` (semana lunes-domingo). */
export function mondayOfWeek(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  const dow = date.getDay(); // 0 = domingo
  const diffToMonday = dow === 0 ? -6 : 1 - dow;
  return addDaysIso(iso, diffToMonday);
}

/** "Lun 16" para encabezados compactos de Mi semana. */
export function shortWeekdayLabel(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number);
  const date = new Date(y, m - 1, d);
  const s = date.toLocaleDateString('es-MX', { weekday: 'short', day: 'numeric' });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** Combina una fecha ISO ("2026-09-14") y una hora "HH:MM" en un datetime
 * naive ("2026-09-14T18:00:00") — el mismo formato sin zona horaria que ya
 * usa el resto de la app para horas de pared (ver wallClockTime). */
export function combineDateTime(dateIso: string, hhmm: string): string {
  return `${dateIso}T${hhmm}:00`;
}

/** Inverso de combineDateTime — para precargar un formulario de edición a
 * partir del datetime que ya vino del backend. */
export function splitDateTime(iso: string): { date: string; time: string } {
  const match = iso.match(/(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})/);
  return match ? { date: match[1], time: `${match[2]}:${match[3]}` } : { date: '', time: '' };
}

/** El backend manda horas de pared sin tzinfo ("2026-09-14T09:00:00") — se
 * leen como texto, nunca vía `new Date(iso)` (que las reinterpretaría en la
 * zona horaria del navegador y correría los horarios). */
export function wallClockTime(iso: string): string {
  const match = iso.match(/T(\d{2}):(\d{2})/);
  return match ? `${match[1]}:${match[2]}` : iso;
}

export function formatDurationMin(min: number): string {
  if (min < 60) return `${min} min`;
  const h = Math.floor(min / 60);
  const rest = min % 60;
  return rest ? `${h}h ${rest}min` : `${h}h`;
}

/** Saludo según la hora local del dispositivo — para el encabezado de Mi día. */
export function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Buenos días';
  if (hour < 19) return 'Buenas tardes';
  return 'Buenas noches';
}

/** "lunes, 16 de noviembre" en español, sin depender de ninguna librería de fechas. */
export function friendlyDate(): string {
  const s = new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' });
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** "HH:MM" en hora de pared local del dispositivo — mismo formato que wallClockTime,
 * para poder comparar directamente contra los bloques del plan. */
export function nowHHMM(): string {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
}

function hhmmToMinutes(hhmm: string): number {
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
}

/**
 * Progreso del día en minutos: cuánto de la duración total de los bloques
 * de hoy ya "pasó" respecto a la hora actual — bloques totalmente
 * anteriores a ahora cuentan completos, el bloque en curso cuenta su
 * fracción transcurrida, los futuros no cuentan nada. Todo en horas de
 * pared (mismo criterio que wallClockTime: nunca `new Date(iso)` directo
 * sobre los horarios que manda el backend, que son naive).
 */
export function dayProgressMinutes(blocks: { start: string; end: string }[]): { doneMin: number; totalMin: number } {
  const now = hhmmToMinutes(nowHHMM());
  let doneMin = 0;
  let totalMin = 0;
  for (const b of blocks) {
    const start = hhmmToMinutes(wallClockTime(b.start));
    const end = hhmmToMinutes(wallClockTime(b.end));
    const duration = Math.max(0, end - start);
    totalMin += duration;
    if (now >= end) doneMin += duration;
    else if (now > start) doneMin += now - start;
  }
  return { doneMin, totalMin };
}
