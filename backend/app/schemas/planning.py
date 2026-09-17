from datetime import date as date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.day_plan import BlockSourceType, ConfidenceLevel


class ReasoningRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_data: str
    system_rule: str
    ai_inference: str
    evidence_ref_id: str | None = None
    confidence: ConfidenceLevel


class PlanBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: BlockSourceType
    source_id: str
    title: str
    start: datetime
    end: datetime
    is_movable: bool


class UnplacedItemRead(BaseModel):
    task_id: str
    title: str
    duration_min: int
    reason: str
    suggestion: str


class ConflictRead(BaseModel):
    message: str
    suggestion: str


class DayPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: date_type
    total_available_min: int
    total_requested_min: int
    unplaced: list[UnplacedItemRead]
    conflicts: list[ConflictRead]
    blocks: list[PlanBlockRead]


class OptimizeRequest(BaseModel):
    date: date_type


class ReplanRequest(BaseModel):
    date: date_type
    reason: str | None = None


class NowResponse(BaseModel):
    situation: str
    message: str
    block_id: str | None = None


class StreakRead(BaseModel):
    current_streak: int
    has_plan_today: bool


class WeekDayRead(BaseModel):
    """
    Un día dentro de GET /v1/planning/week/{start_date} (sección de diseño
    "Mi semana", pedida por Daniel para completar el frontend). Deliberadamente
    más chico que DayPlanRead — sin `unplaced`/`conflicts`, que son detalle
    para la vista de un solo día — y con `has_plan` explícito en vez de
    omitir el objeto entero, para que el cliente pueda distinguir "no
    generado todavía" de "generado y sin bloques".
    """

    date: date_type
    has_plan: bool
    total_available_min: int = 0
    total_requested_min: int = 0
    blocks: list[PlanBlockRead] = []
