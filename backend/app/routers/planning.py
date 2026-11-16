from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.habits import service as habits_service
from app.models.user import User
from app.planning import service
from app.schemas.planning import DayPlanRead, NowResponse, OptimizeRequest, ReplanRequest, StreakRead, WeekDayRead

router = APIRouter(prefix="/v1/planning", tags=["planning"])


def _auto_confirm_habits(current_user: User, db: Session) -> None:
    """
    Dispara habits_service.auto_confirm_due_sessions antes de cualquier
    lectura/generación de plan — así un hábito aparece en el calendario
    (Mi día, Mi semana, "qué hago ahora") sin que el usuario tenga que
    abrir Hábitos y confirmar nada (pedido por Daniel el 12 nov). Siempre
    con la fecha real de HOY (local_now), nunca con la fecha del plan que
    se esté pidiendo — "esta semana" es sobre el calendario real, no sobre
    qué día se está mirando.
    """
    today = service.local_now(current_user).date()
    habits_service.auto_confirm_due_sessions(db, current_user.id, today)


@router.post("/optimize", response_model=DayPlanRead)
def optimize_day(
    payload: OptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    'Optimizar mi día' (sección 7 del brief). Reconstruye el plan completo
    del día desde cero a partir de eventos, disponibilidad, tareas
    pendientes y preferencias — nunca toca días distintos al solicitado.
    """
    _auto_confirm_habits(current_user, db)
    result = service.generate_plan(db, current_user, payload.date)
    day_plan = service.persist_plan(db, current_user, payload.date, result)
    return day_plan


@router.get("/day/{plan_date}", response_model=DayPlanRead)
def read_day(
    plan_date: date_type,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    day_plan = service.get_plan(db, current_user, plan_date)
    if day_plan is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Todavía no hay un plan para ese día — llama primero a /v1/planning/optimize",
        )
    return day_plan


@router.post("/replan", response_model=DayPlanRead)
def replan_day(
    payload: ReplanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Replanificación (sección 8 del brief). Los bloques de tareas cuyo
    inicio ya pasó quedan intactos; solo se reoptimiza lo que queda del
    día. `reason` es informativo por ahora (ej. "no terminé el proyecto")
    — el Módulo 4 (asistente conversacional) lo usará para redactar la
    respuesta en lenguaje natural.
    """
    _auto_confirm_habits(current_user, db)
    now = service.local_now(current_user)
    result = service.generate_replan(db, current_user, payload.date, now)
    day_plan = service.persist_plan(db, current_user, payload.date, result)
    return day_plan


@router.get("/now", response_model=NowResponse)
def whats_next_now(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """'¿Qué hago ahora?' — sección 18 del brief."""
    _auto_confirm_habits(current_user, db)
    now = service.local_now(current_user)
    return service.whats_next(db, current_user, now)


@router.get("/streak", response_model=StreakRead)
def read_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Días consecutivos con un plan generado — calculado de `day_plans`
    real, no un contador de mentira. Pensado para el encabezado de "Mi
    día" en el frontend (sección de diseño: elemento de enganche diario).
    """
    today = service.local_now(current_user).date()
    return service.compute_streak(db, current_user, today)


@router.get("/week/{start_date}", response_model=list[WeekDayRead])
def read_week(
    start_date: date_type,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    'Mi semana': 7 días desde `start_date`, cada uno con sus bloques reales
    si ya tienen un plan generado. Nunca genera planes nuevos — ver
    service.get_week.
    """
    _auto_confirm_habits(current_user, db)
    return service.get_week(db, current_user, start_date)
