from pydantic import BaseModel, ConfigDict, field_validator

HourRange = dict  # {"start": "09:00", "end": "12:00"} — validado abajo


class HourRangeModel(BaseModel):
    start: str
    end: str

    @field_validator("start", "end")
    @classmethod
    def _valid_hhmm(cls, v: str) -> str:
        import datetime

        try:
            datetime.datetime.strptime(v, "%H:%M")
        except ValueError as exc:
            raise ValueError("El formato de hora debe ser HH:MM") from exc
        return v


class PreferencesUpsert(BaseModel):
    preferred_focus_hours: list[HourRangeModel] = []
    preferred_workout_hours: list[HourRangeModel] = []
    preferred_study_hours: list[HourRangeModel] = []
    rest_rules: dict = {}
    blocked_hours_by_activity: dict = {}


class PreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    preferred_focus_hours: list
    preferred_workout_hours: list
    preferred_study_hours: list
    rest_rules: dict
    blocked_hours_by_activity: dict
