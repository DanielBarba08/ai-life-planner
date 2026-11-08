from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.goal import GoalHorizon, GoalStatus


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    horizon: GoalHorizon


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    horizon: GoalHorizon | None = None
    status: GoalStatus | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    horizon: GoalHorizon
    status: GoalStatus
    confirmed_by_user: bool
    created_at: datetime


class GoalCheckinCreate(BaseModel):
    """'¿Cumpliste con tu objetivo hoy?' — la fecha nunca la manda el
    cliente: siempre es "hoy" en la hora de pared del usuario (ver
    app/routers/goals.py, mismo criterio que local_now en planning), para
    que nadie pueda registrar un día pasado o futuro por error."""

    completed: bool


class GoalStreakRead(BaseModel):
    """
    GET/POST /v1/goals/{id}/streak|checkin — racha real de días
    consecutivos confirmados (goal_checkins.completed=True), mismo patrón
    que StreakRead en schemas/planning.py pero por objetivo. Pensada para
    el widget de "Mis rachas" en Mi día (sección de diseño: enganche).
    """

    current_streak: int
    checked_in_today: bool
    completed_today: bool
