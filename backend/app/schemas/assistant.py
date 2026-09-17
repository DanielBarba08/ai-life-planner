from pydantic import BaseModel, ConfigDict, Field

from app.schemas.goal import GoalRead
from app.schemas.planning import DayPlanRead


class AssistantMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AssistantMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str
    reply: str
    day_plan: DayPlanRead | None = None
    goal: GoalRead | None = None
