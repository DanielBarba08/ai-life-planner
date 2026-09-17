"""
Hábitos avanzados (Fase 5 del roadmap). Sigue el mismo principio que el
resto de la capa de servicio de planificación: nunca inventa una sesión
que el usuario no confirmó, y nunca reutiliza una tabla nueva de
"ocurrencias" cuando `tasks.deadline` ya sirve para lo mismo (una sesión
confirmada de un hábito ES una tarea real, con `habit_id` apuntando de
vuelta — ver app/models/habit.py y app/models/task.py).
"""
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.habit import Habit
from app.models.task import Task, TaskStatus
from app.schemas.habit import SuggestedSession


def monday_of(d: date_type) -> date_type:
    return d - timedelta(days=d.weekday())


def week_progress(db: Session, habit: Habit, week_start: date_type) -> dict:
    """
    Progreso real de un hábito en la semana [week_start, week_start + 6]
    (lunes a domingo). 'Confirmadas' son las tareas reales que ya existen
    con `habit_id == habit.id` y `deadline` dentro de ese rango —
    reutiliza el campo que ya tenía `tasks` en vez de inventar una tabla
    de ocurrencias. 'Completadas' es cuántas de esas tienen
    `status == completada` en este momento — el mismo estado ACTUAL que
    usa `app/planning/service.py::compute_personal_stats`, con la misma
    limitación honesta documentada ahí: no hay un timestamp exacto de
    cuándo se completó, solo el estado de hoy.
    """
    week_end = week_start + timedelta(days=6)
    range_start = datetime.combine(week_start, time.min)
    range_end = datetime.combine(week_end, time.max)

    sessions = (
        db.query(Task)
        .filter(Task.habit_id == habit.id, Task.deadline >= range_start, Task.deadline <= range_end)
        .all()
    )
    confirmed = len(sessions)
    completed = sum(1 for t in sessions if t.status == TaskStatus.COMPLETADA)
    remaining = max(0, habit.target_frequency_per_week - confirmed)

    return {
        "week_start": week_start,
        "confirmed_this_week": confirmed,
        "completed_this_week": completed,
        "remaining_to_suggest": remaining,
    }


def suggest_sessions(habit: Habit, week_start: date_type, count: int, today: date_type) -> list[SuggestedSession]:
    """
    Reparte `count` sesiones sugeridas entre los días que quedan de la
    semana — de `today` (o `week_start`, lo que sea más tarde) al domingo
    de esa semana — nunca sugiere un día que ya pasó. Si la semana ya casi
    terminó y no queda ningún día disponible, devuelve una lista vacía en
    vez de amontonar todo en un solo día o proponer algo en el pasado.
    """
    week_end = week_start + timedelta(days=6)
    first_day = max(week_start, today)
    if first_day > week_end or count <= 0:
        return []

    available_days = [first_day + timedelta(days=i) for i in range((week_end - first_day).days + 1)]
    chosen_days = sorted(available_days[i % len(available_days)] for i in range(count))

    return [
        SuggestedSession(
            title=habit.title,
            duration_est_min=habit.duration_est_min,
            concentration_level=habit.concentration_level,
            category=habit.category,
            suggested_date=d,
        )
        for d in chosen_days
    ]


def confirm_sessions(db: Session, habit: Habit, user_id: str, sessions: list[SuggestedSession]) -> list[Task]:
    """
    El único lugar donde una sesión sugerida se vuelve una tarea real —
    siempre a partir de una lista que el usuario ya vio y mandó de vuelta
    explícitamente (punto 14 del brief: nunca crear algo así sin
    confirmación). `deadline` queda al final del día sugerido (23:59): el
    usuario eligió el día, no una hora exacta, así que no se inventa una.
    """
    created: list[Task] = []
    for s in sessions:
        task = Task(
            user_id=user_id,
            habit_id=habit.id,
            title=s.title,
            duration_est_min=s.duration_est_min,
            concentration_level=s.concentration_level,
            category=s.category,
            deadline=datetime.combine(s.suggested_date, time(23, 59)),
        )
        db.add(task)
        created.append(task)
    db.commit()
    for t in created:
        db.refresh(t)
    return created
