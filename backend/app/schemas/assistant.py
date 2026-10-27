from datetime import date as date_type
from datetime import time as time_type
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.availability import AvailabilityType
from app.schemas.goal import GoalRead
from app.schemas.planning import DayPlanRead


class AssistantMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ScheduleItemAvailability(BaseModel):
    """
    Un bloque recurrente propuesto por action=import_schedule (ver
    app/assistant/schedule_extractor.py) — mismo shape que
    AvailabilityBlockCreate (app/schemas/availability.py) salvo por
    `days` (plural): la extracción cubre "lunes a viernes" de un jalón,
    así que aquí vive la lista completa de días y
    app/assistant/service.py::import_schedule_items la expande a un
    AvailabilityBlock por día al confirmar, igual que ya hace el modal de
    Disponibilidad en el frontend (Promise.all por día) — la diferencia es
    que aquí la expansión pasa del lado del servidor.
    """

    kind: Literal["availability"] = "availability"
    label: str = Field(min_length=1, max_length=200)
    type: AvailabilityType
    days: list[int]
    start: time_type
    end: time_type

    @field_validator("days")
    @classmethod
    def _valid_days(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("days no puede estar vacío")
        if any(not 0 <= d <= 6 for d in v):
            raise ValueError("cada día debe estar entre 0 (lunes) y 6 (domingo)")
        return sorted(set(v))

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, end: time_type, info):
        start = info.data.get("start")
        if start and end <= start:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return end


class ScheduleItemEvent(BaseModel):
    """Un evento puntual (fecha concreta, no recurrente) propuesto por
    action=import_schedule — mismo shape que EventCreate salvo por
    separar `date` de `start`/`end` (horas puras), porque así es más
    fácil de revisar/editar en la vista previa que un datetime combinado;
    service.py los combina al confirmar."""

    kind: Literal["event"] = "event"
    label: str = Field(min_length=1, max_length=200)
    date: date_type
    start: time_type
    end: time_type

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, end: time_type, info):
        start = info.data.get("start")
        if start and end <= start:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return end


ScheduleItem = Union[ScheduleItemAvailability, ScheduleItemEvent]
ScheduleItemField = Annotated[ScheduleItem, Field(discriminator="kind")]


class AssistantMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str
    reply: str
    day_plan: DayPlanRead | None = None
    goal: GoalRead | None = None
    # Solo se llena cuando action=import_schedule y sí se logró extraer
    # algo: es una PROPUESTA, nada de esto se guardó todavía — el
    # frontend la muestra con un botón de confirmar/cancelar y, si el
    # usuario confirma, la manda tal cual a POST /v1/assistant/schedule/import
    # (sección 4 del brief: "la IA recomienda, no impone").
    pending_import: list[ScheduleItemField] | None = None


class ScheduleImportRequest(BaseModel):
    items: list[ScheduleItemField] = Field(min_length=1)


class ScheduleImportResponse(BaseModel):
    availability_created: int
    events_created: int
