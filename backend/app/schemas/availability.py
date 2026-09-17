from datetime import time

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.availability import AvailabilityType


class AvailabilityBlockCreate(BaseModel):
    type: AvailabilityType
    day_of_week: int
    start: time
    end: time
    recurring: bool = True

    @field_validator("day_of_week")
    @classmethod
    def _valid_day(cls, v: int) -> int:
        if not 0 <= v <= 6:
            raise ValueError("day_of_week debe estar entre 0 (lunes) y 6 (domingo)")
        return v


class AvailabilityBlockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: AvailabilityType
    day_of_week: int
    start: time
    end: time
    recurring: bool
