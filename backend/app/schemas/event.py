from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.event import EventSource


class EventCreate(BaseModel):
    title: str
    start: datetime
    end: datetime

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, end: datetime, info):
        start = info.data.get("start")
        if start and end <= start:
            raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        return end


class EventUpdate(BaseModel):
    title: str | None = None
    start: datetime | None = None
    end: datetime | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    start: datetime
    end: datetime
    is_movable: bool
    source: EventSource
