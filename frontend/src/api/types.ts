/**
 * Tipos que reflejan los schemas de Pydantic del backend
 * (backend/app/schemas/*.py). Mantenerlos aquí, a mano, en vez de generarlos
 * automáticamente desde el OpenAPI, es una decisión deliberada de alcance
 * del MVP — con 10 recursos es manejable a mano; si el backend crece mucho
 * más, generar esto desde /openapi.json sería lo siguiente.
 */

export type Priority = 'alta' | 'media' | 'baja';
export type ConcentrationLevel = 'alta' | 'media' | 'baja';
export type TaskStatus = 'pendiente' | 'completada' | 'pospuesta';
export type GoalHorizon = 'hoy' | 'semana' | 'mes' | 'largo_plazo';
export type GoalStatus = 'activo' | 'completado' | 'archivado';
export type AvailabilityType = 'trabajo' | 'escuela' | 'personal' | 'comida' | 'aseo' | 'descanso' | 'otro';
export type HabitStatus = 'activo' | 'pausado';
export type ConfidenceLevel = 'alta' | 'media' | 'baja';
export type EvidenceLevel = 'solida' | 'moderada' | 'limitada';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  timezone: string;
  wake_time: string | null; // "HH:MM:SS"
  sleep_time: string | null;
  onboarding_completed: boolean;
  created_at: string;
}

export interface TimeRange {
  start: string; // "HH:MM"
  end: string;
}

export interface UserPreferences {
  user_id: string;
  preferred_focus_hours: TimeRange[];
  preferred_workout_hours: TimeRange[];
  preferred_study_hours: TimeRange[];
  rest_rules: Record<string, unknown>;
  blocked_hours_by_activity: Record<string, unknown>;
}

export interface AvailabilityBlock {
  id: string;
  type: AvailabilityType;
  day_of_week: number; // 0 = lunes
  start: string; // "HH:MM:SS"
  end: string;
  recurring: boolean;
}

export interface FixedEvent {
  id: string;
  title: string;
  start: string; // ISO datetime
  end: string;
  is_movable: boolean;
  source: 'manual' | 'calendario_externo';
}

export interface Task {
  id: string;
  title: string;
  priority: Priority;
  duration_est_min: number;
  concentration_level: ConcentrationLevel;
  category: string | null;
  deadline: string | null;
  status: TaskStatus;
  depends_on_id: string | null;
  habit_id: string | null;
}

export interface Goal {
  id: string;
  title: string;
  horizon: GoalHorizon;
  status: GoalStatus;
  confirmed_by_user: boolean;
  created_at: string;
}

export interface Habit {
  id: string;
  title: string;
  target_frequency_per_week: number;
  duration_est_min: number;
  concentration_level: ConcentrationLevel;
  category: string | null;
  status: HabitStatus;
  goal_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface SuggestedSession {
  title: string;
  duration_est_min: number;
  concentration_level: ConcentrationLevel;
  category: string | null;
  suggested_date: string; // "YYYY-MM-DD"
}

export interface HabitWeek {
  habit_id: string;
  week_start: string;
  target_frequency_per_week: number;
  confirmed_this_week: number;
  completed_this_week: number;
  remaining_to_suggest: number;
  suggested_sessions: SuggestedSession[];
}

export interface PlanBlock {
  id: string;
  source_type: 'event' | 'task';
  source_id: string;
  title: string;
  start: string;
  end: string;
  is_movable: boolean;
}

export interface UnplacedItem {
  task_id: string;
  title: string;
  duration_min: number;
  reason: string;
  suggestion: string;
}

export interface Conflict {
  message: string;
  suggestion: string;
}

export interface DayPlan {
  id: string;
  date: string;
  total_available_min: number;
  total_requested_min: number;
  unplaced: UnplacedItem[];
  conflicts: Conflict[];
  blocks: PlanBlock[];
}

export interface EvidenceRead {
  claim: string;
  source: string;
  authors: string;
  year: number;
  study_type: string;
  doi: string | null;
  evidence_level: EvidenceLevel;
  limitations: string;
}

export interface GeneralEvidenceRead {
  topic: string;
  system_rule: string;
  evidence: EvidenceRead;
}

export interface ExplanationRead {
  block_id: string;
  block_title: string;
  block_start: string;
  block_end: string;
  user_data: string;
  system_rule: string;
  evidence: EvidenceRead | null;
  ai_inference: string;
  confidence: ConfidenceLevel;
}

export interface Streak {
  current_streak: number;
  has_plan_today: boolean;
}

export interface WeekDay {
  date: string;
  has_plan: boolean;
  total_available_min: number;
  total_requested_min: number;
  blocks: PlanBlock[];
}

export interface WhatsNext {
  situation: 'en_curso' | 'hueco_libre' | 'dia_libre';
  message: string;
  block_id: string | null;
}

export interface AssistantResponse {
  action: string;
  reply: string;
  day_plan: DayPlan | null;
  goal: Goal | null;
}

export interface ApiError {
  detail: string;
}
