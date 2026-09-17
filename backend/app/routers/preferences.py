from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.preferences import UserPreferences
from app.models.user import User
from app.schemas.preferences import PreferencesRead, PreferencesUpsert

router = APIRouter(prefix="/v1/users/me/preferences", tags=["preferences"])


def _get_or_create(db: Session, user: User) -> UserPreferences:
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("", response_model=PreferencesRead)
def read_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_or_create(db, current_user)


@router.put("", response_model=PreferencesRead)
def upsert_preferences(
    payload: PreferencesUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    PUT reemplaza el documento completo de preferencias — el onboarding
    progresivo (punto 5 del brief) siempre manda el objeto entero desde el
    cliente, así que no necesitamos un PATCH parcial aquí todavía.
    """
    prefs = _get_or_create(db, current_user)
    prefs.preferred_focus_hours = [h.model_dump() for h in payload.preferred_focus_hours]
    prefs.preferred_workout_hours = [h.model_dump() for h in payload.preferred_workout_hours]
    prefs.preferred_study_hours = [h.model_dump() for h in payload.preferred_study_hours]
    prefs.rest_rules = payload.rest_rules
    prefs.blocked_hours_by_activity = payload.blocked_hours_by_activity
    db.commit()
    db.refresh(prefs)
    return prefs
