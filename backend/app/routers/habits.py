from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.habits import service as habits_service
from app.models.goal import Goal
from app.models.habit import Habit, HabitStatus
from app.models.user import User
from app.planning.service import local_now
from app.schemas.habit import ConfirmWeekRequest, HabitCreate, HabitRead, HabitUpdate, HabitWeekRead
from app.schemas.task import TaskRead

router = APIRouter(prefix="/v1/habits", tags=["habits"])


def _get_owned_habit(db: Session, habit_id: str, user_id: str) -> Habit:
    habit = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if habit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Hábito no encontrado")
    return habit


def _validate_goal(db: Session, goal_id: str | None, user_id: str):
    if goal_id is None:
        return
    goal = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if goal is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="goal_id debe ser un objetivo existente del mismo usuario",
        )


@router.get("", response_model=list[HabitRead])
def list_habits(
    status_filter: HabitStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Habit).filter(Habit.user_id == current_user.id)
    if status_filter is not None:
        query = query.filter(Habit.status == status_filter)
    return query.order_by(Habit.created_at).all()


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(
    payload: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_goal(db, payload.goal_id, current_user.id)
    habit = Habit(user_id=current_user.id, **payload.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get("/{habit_id}", response_model=HabitRead)
def read_habit(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_owned_habit(db, habit_id, current_user.id)


@router.patch("/{habit_id}", response_model=HabitRead)
def update_habit(
    habit_id: str,
    payload: HabitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habit = _get_owned_habit(db, habit_id, current_user.id)
    updates = payload.model_dump(exclude_unset=True)

    if "goal_id" in updates:
        _validate_goal(db, updates["goal_id"], current_user.id)

    for field, value in updates.items():
        setattr(habit, field, value)

    db.commit()
    db.refresh(habit)
    return habit


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    habit = _get_owned_habit(db, habit_id, current_user.id)
    db.delete(habit)
    db.commit()
    return None


@router.get("/{habit_id}/week", response_model=HabitWeekRead)
def read_habit_week(
    habit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Progreso real de la semana ACTUAL (lunes de "hoy" en la hora de pared
    del usuario — mismo criterio que el resto del Planning Engine, ver
    app/planning/service.py::local_now) + sesiones propuestas para
    completar lo que falte (nunca creadas todavía — ver POST
    .../confirm-week). Deliberadamente sin parámetro para consultar otras
    semanas todavía — ver semanas pasadas/futuras de un hábito es Fase 5+
    (mismo tipo de límite que "Disponibilidad" solo permite crear, no
    editar, documentado en el README en vez de disimulado).
    """
    habit = _get_owned_habit(db, habit_id, current_user.id)
    today = local_now(current_user).date()
    start = habits_service.monday_of(today)

    progress = habits_service.week_progress(db, habit, start)
    suggested = habits_service.suggest_sessions(habit, start, progress["remaining_to_suggest"], today)

    return HabitWeekRead(
        habit_id=habit.id,
        week_start=progress["week_start"],
        target_frequency_per_week=habit.target_frequency_per_week,
        confirmed_this_week=progress["confirmed_this_week"],
        completed_this_week=progress["completed_this_week"],
        remaining_to_suggest=progress["remaining_to_suggest"],
        suggested_sessions=suggested,
    )


@router.post("/{habit_id}/confirm-week", response_model=list[TaskRead], status_code=status.HTTP_201_CREATED)
def confirm_habit_week(
    habit_id: str,
    payload: ConfirmWeekRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Convierte en tareas reales las sesiones que el usuario ya vio (vía GET
    .../week) y decidió confirmar — el único punto donde esto pasa (punto
    14 del brief). El cliente manda de vuelta exactamente las sesiones que
    quiere (puede ser un subconjunto de lo sugerido, nunca más de lo que
    el propio hábito necesita: se valida contra lo que de verdad falta).
    """
    habit = _get_owned_habit(db, habit_id, current_user.id)
    today = local_now(current_user).date()
    week_start = habits_service.monday_of(today)
    progress = habits_service.week_progress(db, habit, week_start)

    if len(payload.sessions) > progress["remaining_to_suggest"]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Solo faltan {progress['remaining_to_suggest']} sesiones por confirmar esta semana, "
                f"se mandaron {len(payload.sessions)}."
            ),
        )

    return habits_service.confirm_sessions(db, habit, current_user.id, payload.sessions)
