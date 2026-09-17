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
