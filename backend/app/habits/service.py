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

from app.models.habit import Habit, HabitStatus
from app.models.task import Task, TaskStatus
from app.schemas.habit import HabitProgressWeek, SuggestedSession


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


def suggest_sessions(
    habit: Habit,
    week_start: date_type,
    count: int,
    today: date_type,
    exclude_dates: set[date_type] | None = None,
) -> list[SuggestedSession]:
    """
    Reparte `count` sesiones sugeridas entre los días que quedan de la
    semana — de `today` (o `week_start`, lo que sea más tarde) al domingo
    de esa semana — nunca sugiere un día que ya pasó. Si la semana ya casi
    terminó y no queda ningún día disponible, devuelve una lista vacía en
    vez de amontonar todo en un solo día o proponer algo en el pasado.

    Un día nunca recibe más de una sesión sugerida: si quedan menos días
    disponibles que `count` (por ejemplo, se pide esto un sábado o
    domingo, con la semana casi terminada), se sugieren menos de `count`
    sesiones — máximo una por día — en vez de repetir un mismo día varias
    veces (bug reportado por Daniel el 8 nov: "se agregan todas las horas
    en un solo día").

    `exclude_dates` son días que ya tienen una sesión CONFIRMADA de este
    hábito esta semana (ver auto_confirm_due_sessions) — sin esto, un
    hábito con `target_frequency_per_week` mayor a los días que quedan en
    la semana (ej. 3x/semana creado un sábado, con solo 2 días
    disponibles) volvería a sugerir esos mismos 2 días ya confirmados en
    cada llamada siguiente, duplicando la sesión del mismo día — la
    versión automática del bug del 8 nov, ahora disparada por cada
    lectura en vez de por un tap manual.
    """
    week_end = week_start + timedelta(days=6)
    first_day = max(week_start, today)
    if first_day > week_end or count <= 0:
        return []

    available_days = [first_day + timedelta(days=i) for i in range((week_end - first_day).days + 1)]
    if exclude_dates:
        available_days = [d for d in available_days if d not in exclude_dates]
    chosen_days = sorted(available_days[: min(count, len(available_days))])

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


def confirmed_dates_this_week(db: Session, habit: Habit, week_start: date_type) -> set[date_type]:
    """Días de esta semana que ya tienen una tarea real confirmada de este
    hábito — ver el docstring de suggest_sessions sobre por qué hace falta
    excluirlos antes de volver a sugerir/confirmar."""
    week_end = week_start + timedelta(days=6)
    range_start = datetime.combine(week_start, time.min)
    range_end = datetime.combine(week_end, time.max)
    rows = (
        db.query(Task.deadline)
        .filter(Task.habit_id == habit.id, Task.deadline >= range_start, Task.deadline <= range_end)
        .all()
    )
    return {deadline.date() for (deadline,) in rows if deadline is not None}


def auto_confirm_due_sessions(db: Session, user_id: str, today: date_type) -> list[Task]:
    """
    Agrega solas al horario las sesiones que le falten a cada hábito
    ACTIVO esta semana — pedido por Daniel el 12 nov ("que se agreguen al
    horario") para no tener que entrar a Hábitos y tocar "confirmar" cada
    semana. Se llama al leer cualquier vista que muestre hábitos o el
    calendario (ver app/routers/habits.py y app/routers/planning.py), así
    que como mucho tarda una lectura en reflejarse — es idempotente: si
    ya no falta nada (`remaining_to_suggest == 0`, incluyendo el caso de
    haberse llamado ya en el mismo request), no hace ninguna escritura.

    Un hábito PAUSADO nunca se toca aquí — pausarlo es justo la forma que
    tiene el usuario de decir "no quiero que esto me siga apareciendo
    solo en el calendario esta semana".

    Sigue sin inventar nada nuevo: reutiliza exactamente
    suggest_sessions/confirm_sessions, los mismos que ya validaba el
    flujo manual — la única diferencia es quién los dispara.
    """
    week_start = monday_of(today)
    habits = db.query(Habit).filter(Habit.user_id == user_id, Habit.status == HabitStatus.ACTIVO).all()

    created: list[Task] = []
    for habit in habits:
        progress = week_progress(db, habit, week_start)
        remaining = progress["remaining_to_suggest"]
        if remaining <= 0:
            continue
        sessions = suggest_sessions(
            habit, week_start, remaining, today, exclude_dates=confirmed_dates_this_week(db, habit, week_start)
        )
        if sessions:
            created.extend(confirm_sessions(db, habit, user_id, sessions))
    return created


def progress_history(db: Session, habit: Habit, today: date_type, weeks: int = 6) -> list[HabitProgressWeek]:
    """
    Progreso real de las últimas `weeks` semanas (incluyendo la actual),
    de más antigua a más reciente — para la gráfica de "progreso en las
    semanas" que pidió Daniel el 12 nov en Hábitos. Cada punto reutiliza
    week_progress tal cual (mismas tareas reales con habit_id, nunca un
    número inventado); semanas sin ninguna sesión confirmada simplemente
    quedan en 0, no se rellenan con datos de otra semana.
    """
    current_monday = monday_of(today)
    result: list[HabitProgressWeek] = []
    for i in range(weeks - 1, -1, -1):
        week_start = current_monday - timedelta(weeks=i)
        progress = week_progress(db, habit, week_start)
        result.append(
            HabitProgressWeek(
                week_start=week_start,
                target_frequency_per_week=habit.target_frequency_per_week,
                confirmed=progress["confirmed_this_week"],
                completed=progress["completed_this_week"],
            )
        )
    return result


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
