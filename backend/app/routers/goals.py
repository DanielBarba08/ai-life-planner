from datetime import date as date_type
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.goal import Goal, GoalCheckin, GoalStatus
from app.models.user import User
from app.planning.service import local_now
from app.schemas.goal import GoalCheckinCreate, GoalCreate, GoalRead, GoalStreakRead, GoalUpdate

router = APIRouter(prefix="/v1/goals", tags=["goals"])


def _get_owned_goal(db: Session, goal_id: str, user_id: str) -> Goal:
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if goal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Objetivo no encontrado")
    return goal


def _compute_streak(db: Session, goal_id: str, today: date_type) -> GoalStreakRead:
    """
    Mismo criterio "indulgente" que compute_streak en
    app/planning/service.py (si hoy todavía no se contestó, no corta la
    racha sola — cuenta desde ayer) CON una diferencia: aquí sí puede haber
    una respuesta explícita de "no" para hoy, y esa SÍ corta la racha de
    inmediato a 0 (no es lo mismo "no he abierto la app" que "hoy no
    cumplí").
    """
    rows = db.query(GoalCheckin.date, GoalCheckin.completed).filter(
        GoalCheckin.goal_id == goal_id, GoalCheckin.date <= today
    ).all()
    completed_dates = {d for d, done in rows if done}
    answered_dates = {d for d, _ in rows}

    checked_in_today = today in answered_dates
    completed_today = today in completed_dates

    if checked_in_today and not completed_today:
        streak = 0
    else:
        cursor = today if completed_today else today - timedelta(days=1)
        streak = 0
        while cursor in completed_dates:
            streak += 1
            cursor -= timedelta(days=1)

    return GoalStreakRead(current_streak=streak, checked_in_today=checked_in_today, completed_today=completed_today)


@router.get("", response_model=list[GoalRead])
def list_goals(
    status_filter: GoalStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Goal).filter(Goal.user_id == current_user.id)
    if status_filter is not None:
        query = query.filter(Goal.status == status_filter)
    return query.order_by(Goal.created_at.desc()).all()


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # confirmed_by_user siempre True aquí: en este módulo el usuario es
    # quien crea el objetivo directamente (ver nota en app/models/goal.py).
    goal = Goal(user_id=current_user.id, confirmed_by_user=True, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.get("/{goal_id}", response_model=GoalRead)
def read_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_goal(db, goal_id, current_user.id)


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = _get_owned_goal(db, goal_id, current_user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = _get_owned_goal(db, goal_id, current_user.id)
    db.delete(goal)
    db.commit()
    return None


@router.get("/{goal_id}/streak", response_model=GoalStreakRead)
def read_goal_streak(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = _get_owned_goal(db, goal_id, current_user.id)
    today = local_now(current_user).date()
    return _compute_streak(db, goal.id, today)


@router.post("/{goal_id}/checkin", response_model=GoalStreakRead)
def checkin_goal(
    goal_id: str,
    payload: GoalCheckinCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = _get_owned_goal(db, goal_id, current_user.id)
    today = local_now(current_user).date()

    existing = db.query(GoalCheckin).filter(GoalCheckin.goal_id == goal.id, GoalCheckin.date == today).first()
    if existing is not None:
        existing.completed = payload.completed
    else:
        db.add(GoalCheckin(goal_id=goal.id, date=today, completed=payload.completed))
    db.commit()

    return _compute_streak(db, goal.id, today)
