from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import ConcentrationLevel, Priority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: Priority = Priority.MEDIA
    duration_est_min: int = Field(gt=0, le=24 * 60)
    concentration_level: ConcentrationLevel = ConcentrationLevel.MEDIA
    category: str | None = Field(default=None, max_length=80)
    deadline: datetime | None = None
    depends_on_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    priority: Priority | None = None
    duration_est_min: int | None = Field(default=None, gt=0, le=24 * 60)
    concentration_level: ConcentrationLevel | None = None
    category: str | None = None
    deadline: datetime | None = None
    status: TaskStatus | None = None
    depends_on_id: str | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    priority: Priority
    duration_est_min: int
    concentration_level: ConcentrationLevel
    category: str | None
    deadline: datetime | None
    status: TaskStatus
    depends_on_id: str | None
    habit_id: str | None
    created_at: datetime
    updated_at: datetime
