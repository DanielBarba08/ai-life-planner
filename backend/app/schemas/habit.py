from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.habit import HabitStatus
from app.models.task import ConcentrationLevel


class HabitCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    target_frequency_per_week: int = Field(ge=1, le=14)
    duration_est_min: int = Field(gt=0, le=24 * 60)
    concentration_level: ConcentrationLevel = ConcentrationLevel.MEDIA
    category: str | None = Field(default=None, max_length=80)
    goal_id: str | None = None


class HabitUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    target_frequency_per_week: int | None = Field(default=None, ge=1, le=14)
    duration_est_min: int | None = Field(default=None, gt=0, le=24 * 60)
    concentration_level: ConcentrationLevel | None = None
    category: str | None = None
    status: HabitStatus | None = None
    goal_id: str | None = None


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    target_frequency_per_week: int
    duration_est_min: int
    concentration_level: ConcentrationLevel
    category: str | None
    status: HabitStatus
    goal_id: str | None
    created_at: datetime
    updated_at: datetime


class SuggestedSession(BaseModel):
    """
    Una sesión PROPUESTA para completar el hábito esta semana — no existe
    en ningún lado hasta que el usuario la confirma (POST .../confirm-week,
    ver app/habits/service.py). `suggested_date` nunca cae antes de hoy ni
    después del domingo de la semana consultada.
    """

    title: str
    duration_est_min: int
    concentration_level: ConcentrationLevel
    category: str | None
    suggested_date: date_type


class HabitWeekRead(BaseModel):
    """
    Progreso real de un hábito en la semana de `week_start` (lunes),
    GET /v1/habits/{id}/week. `confirmed_this_week` / `completed_this_week`
    se calculan de tareas reales con `habit_id` y `deadline` dentro de esa
    semana (ver app/habits/service.py::week_progress) — nunca un contador
    simulado. `suggested_sessions` solo trae borradores cuando todavía
    faltan sesiones por confirmar esta semana (`remaining_to_suggest > 0`).
    """

    habit_id: str
    week_start: date_type
    target_frequency_per_week: int
    confirmed_this_week: int
    completed_this_week: int
    remaining_to_suggest: int
    suggested_sessions: list[SuggestedSession]


class ConfirmWeekRequest(BaseModel):
    sessions: list[SuggestedSession]
