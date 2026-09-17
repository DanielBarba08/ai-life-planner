import { api } from './client';
import type {
  AssistantResponse,
  AuthTokens,
  AvailabilityBlock,
  AvailabilityType,
  ConcentrationLevel,
  Conflict,
  DayPlan,
  EvidenceLevel,
  ExplanationRead,
  FixedEvent,
  GeneralEvidenceRead,
  Goal,
  GoalHorizon,
  GoalStatus,
  Habit,
  HabitStatus,
  HabitWeek,
  Priority,
  Streak,
  SuggestedSession,
  Task,
  TaskStatus,
  TimeRange,
  UnplacedItem,
  User,
  UserPreferences,
  WeekDay,
  WhatsNext,
} from './types';

// -- auth --------------------------------------------------------------
export const authApi = {
  register: (body: { email: string; password: string; name?: string; timezone?: string }) =>
    api.post<User>('/v1/auth/register', body).then((r) => r.data),
  login: (body: { email: string; password: string }) =>
    api.post<AuthTokens>('/v1/auth/login', body).then((r) => r.data),
};

// -- users ---------------------------------------------------------------
export const usersApi = {
  me: () => api.get<User>('/v1/users/me').then((r) => r.data),
  update: (body: Partial<Pick<User, 'name' | 'timezone' | 'wake_time' | 'sleep_time' | 'onboarding_completed'>>) =>
    api.patch<User>('/v1/users/me', body).then((r) => r.data),
  deleteAccount: () => api.delete('/v1/users/me'),
};

// -- preferences -----------------------------------------------------------
export const preferencesApi = {
  get: () => api.get<UserPreferences>('/v1/users/me/preferences').then((r) => r.data),
  put: (body: {
    preferred_focus_hours?: TimeRange[];
    preferred_workout_hours?: TimeRange[];
    preferred_study_hours?: TimeRange[];
    rest_rules?: Record<string, unknown>;
    blocked_hours_by_activity?: Record<string, unknown>;
  }) => api.put<UserPreferences>('/v1/users/me/preferences', body).then((r) => r.data),
};

// -- availability ----------------------------------------------------------
export const availabilityApi = {
  list: () => api.get<AvailabilityBlock[]>('/v1/availability').then((r) => r.data),
  create: (body: { type: AvailabilityType; day_of_week: number; start: string; end: string }) =>
    api.post<AvailabilityBlock>('/v1/availability', body).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/availability/${id}`),
};

// -- events ----------------------------------------------------------------
export const eventsApi = {
  list: () => api.get<FixedEvent[]>('/v1/events').then((r) => r.data),
  create: (body: { title: string; start: string; end: string }) =>
    api.post<FixedEvent>('/v1/events', body).then((r) => r.data),
  update: (id: string, body: Partial<{ title: string; start: string; end: string }>) =>
    api.patch<FixedEvent>(`/v1/events/${id}`, body).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/events/${id}`),
};

// -- tasks -------------------------------------------------------------------
export const tasksApi = {
  list: (params?: { status?: TaskStatus; category?: string }) =>
    api.get<Task[]>('/v1/tasks', { params }).then((r) => r.data),
  create: (body: {
    title: string;
    priority?: Priority;
    duration_est_min: number;
    concentration_level?: ConcentrationLevel;
    category?: string | null;
    deadline?: string | null;
    depends_on_id?: string | null;
  }) => api.post<Task>('/v1/tasks', body).then((r) => r.data),
  update: (id: string, body: Partial<Task>) => api.patch<Task>(`/v1/tasks/${id}`, body).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/tasks/${id}`),
};

// -- goals -------------------------------------------------------------------
export const goalsApi = {
  list: (params?: { status?: GoalStatus }) => api.get<Goal[]>('/v1/goals', { params }).then((r) => r.data),
  create: (body: { title: string; horizon: GoalHorizon }) => api.post<Goal>('/v1/goals', body).then((r) => r.data),
  update: (id: string, body: Partial<{ title: string; horizon: GoalHorizon; status: GoalStatus }>) =>
    api.patch<Goal>(`/v1/goals/${id}`, body).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/goals/${id}`),
};

// -- habits (Fase 5 — hábitos avanzados) --------------------------------------
export const habitsApi = {
  list: (params?: { status?: HabitStatus }) => api.get<Habit[]>('/v1/habits', { params }).then((r) => r.data),
  create: (body: {
    title: string;
    target_frequency_per_week: number;
    duration_est_min: number;
    concentration_level?: ConcentrationLevel;
    category?: string | null;
    goal_id?: string | null;
  }) => api.post<Habit>('/v1/habits', body).then((r) => r.data),
  update: (
    id: string,
    body: Partial<{
      title: string;
      target_frequency_per_week: number;
      duration_est_min: number;
      concentration_level: ConcentrationLevel;
      category: string | null;
      status: HabitStatus;
      goal_id: string | null;
    }>,
  ) => api.patch<Habit>(`/v1/habits/${id}`, body).then((r) => r.data),
  remove: (id: string) => api.delete(`/v1/habits/${id}`),
  week: (id: string) => api.get<HabitWeek>(`/v1/habits/${id}/week`).then((r) => r.data),
  confirmWeek: (id: string, sessions: SuggestedSession[]) =>
    api.post<Task[]>(`/v1/habits/${id}/confirm-week`, { sessions }).then((r) => r.data),
};

// -- planning ----------------------------------------------------------------
export const planningApi = {
  optimize: (date: string) => api.post<DayPlan>('/v1/planning/optimize', { date }).then((r) => r.data),
  getDay: (date: string) => api.get<DayPlan>(`/v1/planning/day/${date}`).then((r) => r.data),
  replan: (date: string, reason?: string) =>
    api.post<DayPlan>('/v1/planning/replan', { date, reason }).then((r) => r.data),
  now: () => api.get<WhatsNext>('/v1/planning/now').then((r) => r.data),
  streak: () => api.get<Streak>('/v1/planning/streak').then((r) => r.data),
  week: (startDate: string) => api.get<WeekDay[]>(`/v1/planning/week/${startDate}`).then((r) => r.data),
};

// -- explanations --------------------------------------------------------------
export const explanationsApi = {
  get: (blockId: string) => api.get<ExplanationRead>(`/v1/explanations/${blockId}`).then((r) => r.data),
  general: () => api.get<GeneralEvidenceRead[]>('/v1/explanations/general').then((r) => r.data),
};

// -- assistant -------------------------------------------------------------------
export const assistantApi = {
  send: (message: string) => api.post<AssistantResponse>('/v1/assistant/message', { message }).then((r) => r.data),
};

export type { Conflict, EvidenceLevel, UnplacedItem };
