"""
Capa de servicio: traduce entre la base de datos y el motor puro de
app/planning/engine.py. El motor no sabe que SQLAlchemy existe; este
archivo es el único que sabe de ambos mundos.
"""
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.availability import AvailabilityBlock
from app.models.day_plan import BlockSourceType, ConfidenceLevel, DayPlan, PlanBlock, RecommendationExplanation
from app.models.event import FixedEvent
from app.models.preferences import UserPreferences
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.planning import engine
from app.planning.evidence import find_evidence_for_label

DEFAULT_WAKE_TIME = time(7, 0)
DEFAULT_SLEEP_TIME = time(23, 0)


def _parse_hour(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def _hour_ranges(raw: list[dict] | None) -> list[tuple[time, time]]:
    if not raw:
        return []
    return [(_parse_hour(r["start"]), _parse_hour(r["end"])) for r in raw]


def _build_preferences(prefs: UserPreferences | None) -> engine.PreferenceWindows:
    if prefs is None:
        return engine.PreferenceWindows()
    min_break = 10
    if isinstance(prefs.rest_rules, dict) and "min_break_between_blocks_min" in prefs.rest_rules:
        min_break = int(prefs.rest_rules["min_break_between_blocks_min"])
    return engine.PreferenceWindows(
        focus=_hour_ranges(prefs.preferred_focus_hours),
        study=_hour_ranges(prefs.preferred_study_hours),
        workout=_hour_ranges(prefs.preferred_workout_hours),
        min_break_min=min_break,
    )


def _build_fixed_items(db: Session, user: User, target_date: date_type) -> list[engine.FixedItem]:
    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)

    events = (
        db.query(FixedEvent)
        .filter(FixedEvent.user_id == user.id, FixedEvent.start >= day_start, FixedEvent.start <= day_end)
        .all()
    )
    fixed_items = [engine.FixedItem(e.id, e.title, e.start, e.end) for e in events]

    weekday = target_date.weekday()  # 0 = lunes, igual que availability_blocks.day_of_week
    availability = (
        db.query(AvailabilityBlock)
        .filter(AvailabilityBlock.user_id == user.id, AvailabilityBlock.day_of_week == weekday)
        .all()
    )
    fixed_items += [
        engine.FixedItem(
            f"availability:{a.id}",
            f"{a.type.value.capitalize()} (recurrente)",
            datetime.combine(target_date, a.start),
            datetime.combine(target_date, a.end),
        )
        for a in availability
    ]
    return fixed_items


def _build_task_items(db: Session, user: User) -> tuple[list[engine.TaskItem], set[str]]:
    pending = db.query(Task).filter(Task.user_id == user.id, Task.status == TaskStatus.PENDIENTE).all()
    pending_ids = {t.id for t in pending}
    items = [
        engine.TaskItem(
            id=t.id,
            title=t.title,
            priority=t.priority.value,
            duration_min=t.duration_est_min,
            concentration_level=t.concentration_level.value,
            category=t.category,
            deadline=t.deadline,
            depends_on_id=t.depends_on_id,
        )
        for t in pending
    ]
    return items, pending_ids


def _wake_sleep(user: User) -> tuple[time, time]:
    return (user.wake_time or DEFAULT_WAKE_TIME, user.sleep_time or DEFAULT_SLEEP_TIME)


def local_now(user: User) -> datetime:
    """
    'Ahora', en hora de pared del usuario (naive, sin tzinfo) — así se
    puede comparar directamente contra block.start/end, que también son
    horas de pared locales (vienen de combinar `date` con `time` puros,
    sin zona horaria — ver _build_fixed_items y build_day_plan).
    """
    try:
        tz = ZoneInfo(user.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        tz = ZoneInfo("UTC")
    return datetime.now(tz).replace(tzinfo=None)


def generate_plan(db: Session, user: User, target_date: date_type) -> engine.DayPlanResult:
    """'Optimizar mi día': construye el plan completo desde cero."""
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    wake_time, sleep_time = _wake_sleep(user)
    fixed_items = _build_fixed_items(db, user, target_date)
    tasks, pending_ids = _build_task_items(db, user)
    personal_stats = compute_personal_stats(db, user, target_date)

    return engine.build_day_plan(
        target_date=target_date,
        wake_time=wake_time,
        sleep_time=sleep_time,
        fixed_items=fixed_items,
        tasks=tasks,
        pending_task_ids=pending_ids,
        preferences=_build_preferences(prefs),
        personal_stats=personal_stats,
    )


def generate_replan(db: Session, user: User, target_date: date_type, now: datetime) -> engine.DayPlanResult:
    """
    Replanificación parcial: los bloques de tareas cuyo inicio ya pasó
    quedan bloqueados tal cual; solo se reoptimiza la ventana restante,
    con las tareas que sigan pendientes en ese momento.
    """
    existing = (
        db.query(DayPlan)
        .filter(DayPlan.user_id == user.id, DayPlan.date == target_date)
        .first()
    )

    locked_blocks: list[engine.PlannedBlock] = []
    locked_task_ids: set[str] = set()
    if existing:
        for block in existing.blocks:
            if block.source_type == BlockSourceType.TASK and block.start < now:
                reasoning = None
                if block.explanation:
                    reasoning = engine.ReasoningTrace(
                        user_data=block.explanation.user_data_snippet,
                        system_rule=block.explanation.system_rule_snippet,
                        ai_inference=block.explanation.ai_inference_snippet,
                        confidence=block.explanation.confidence.value,
                        # Un bloque bloqueado ya pasó — conserva la evidencia y la
                        # etiqueta de preferencia que ya tenía en vez de
                        # resolverlas de nuevo (matched_preference_label sí se
                        # persiste desde la migración 16e005952f99; para planes
                        # más viejos queda None, que es lo correcto).
                        evidence_ref_id=block.explanation.evidence_ref_id,
                        matched_preference_label=block.explanation.matched_preference_label,
                    )
                locked_blocks.append(
                    engine.PlannedBlock(
                        "task", block.source_id, block.title, block.start, block.end, block.is_movable, reasoning
                    )
                )
                locked_task_ids.add(block.source_id)

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
    wake_time, sleep_time = _wake_sleep(user)
    fixed_items = _build_fixed_items(db, user, target_date)
    tasks, pending_ids = _build_task_items(db, user)
    pending_ids -= locked_task_ids
    personal_stats = compute_personal_stats(db, user, target_date)

    return engine.build_day_plan(
        target_date=target_date,
        wake_time=wake_time,
        sleep_time=sleep_time,
        fixed_items=fixed_items,
        tasks=tasks,
        pending_task_ids=pending_ids,
        preferences=_build_preferences(prefs),
        locked_blocks=locked_blocks,
        min_start=now,
        personal_stats=personal_stats,
    )


def persist_plan(db: Session, user: User, target_date: date_type, result: engine.DayPlanResult) -> DayPlan:
    """Reemplaza (o crea) el DayPlan de esta fecha con el resultado fresco del motor."""
    existing = db.query(DayPlan).filter(DayPlan.user_id == user.id, DayPlan.date == target_date).first()
    if existing:
        db.delete(existing)
        db.flush()

    day_plan = DayPlan(
        user_id=user.id,
        date=target_date,
        total_available_min=result.total_available_min,
        total_requested_min=result.total_requested_min,
        unplaced=[
            {
                "task_id": u.task_id,
                "title": u.title,
                "duration_min": u.duration_min,
                "reason": u.reason,
                "suggestion": u.suggestion,
            }
            for u in result.unplaced
        ],
        conflicts=[{"message": c.message, "suggestion": c.suggestion} for c in result.conflicts],
    )
    db.add(day_plan)
    db.flush()

    for b in result.blocks:
        block = PlanBlock(
            day_plan_id=day_plan.id,
            source_type=BlockSourceType.TASK if b.source_type == "task" else BlockSourceType.EVENT,
            source_id=b.source_id,
            title=b.title,
            start=b.start,
            end=b.end,
            is_movable=b.is_movable,
        )
        db.add(block)
        db.flush()
        if b.reasoning:
            # Si el bloque ya traía un evidence_ref_id (viene de un bloque
            # bloqueado en una replanificación), se conserva tal cual. Si no,
            # se resuelve por primera vez a partir de la ventana de
            # preferencia que de verdad se usó — nunca al revés (nunca se
            # inventa una etiqueta a partir de una evidencia).
            evidence_ref_id = b.reasoning.evidence_ref_id
            if evidence_ref_id is None and b.reasoning.matched_preference_label:
                evidence = find_evidence_for_label(db, b.reasoning.matched_preference_label)
                evidence_ref_id = evidence.id if evidence else None

            db.add(
                RecommendationExplanation(
                    plan_block_id=block.id,
                    user_data_snippet=b.reasoning.user_data,
                    system_rule_snippet=b.reasoning.system_rule,
                    evidence_ref_id=evidence_ref_id,
                    ai_inference_snippet=b.reasoning.ai_inference,
                    confidence=ConfidenceLevel(b.reasoning.confidence),
                    # Personal Productivity Model — ver migración
                    # 16e005952f99 y compute_personal_stats más abajo.
                    matched_preference_label=b.reasoning.matched_preference_label,
                )
            )

    db.commit()
    db.refresh(day_plan)
    return day_plan


def get_plan(db: Session, user: User, target_date: date_type) -> DayPlan | None:
    return db.query(DayPlan).filter(DayPlan.user_id == user.id, DayPlan.date == target_date).first()


def get_week(db: Session, user: User, start_date: date_type) -> list[dict]:
    """
    'Mi semana' (hueco de API identificado al construir el frontend, ver
    frontend/README.md): 7 días consecutivos empezando en `start_date`, con
    los bloques REALES de cada día que ya tiene un plan generado — nunca
    genera planes nuevos aquí (eso lo sigue haciendo /v1/planning/optimize,
    un día a la vez, a petición explícita del usuario). Un día sin plan
    todavía viene con `has_plan=False` y sin bloques, no con datos
    inventados.
    """
    end_date = start_date + timedelta(days=6)
    plans = {
        p.date: p
        for p in db.query(DayPlan)
        .filter(DayPlan.user_id == user.id, DayPlan.date >= start_date, DayPlan.date <= end_date)
        .all()
    }

    days = []
    for i in range(7):
        d = start_date + timedelta(days=i)
        plan = plans.get(d)
        if plan is None:
            days.append({"date": d, "has_plan": False, "total_available_min": 0, "total_requested_min": 0, "blocks": []})
        else:
            days.append(
                {
                    "date": d,
                    "has_plan": True,
                    "total_available_min": plan.total_available_min,
                    "total_requested_min": plan.total_requested_min,
                    "blocks": sorted(plan.blocks, key=lambda b: b.start),
                }
            )
    return days


def compute_personal_stats(db: Session, user: User, target_date: date_type) -> dict[str, engine.LabelStats]:
    """
    Personal Productivity Model (Fase 3 del roadmap): historial REAL de
    finalización por ventana de preferencia, calculado a partir de
    `recommendation_explanations.matched_preference_label` (persistido
    desde la migración 16e005952f99) cruzado con el estado ACTUAL de cada
    tarea (`tasks.status`).

    Limitación explícita, igual de honesta que la documentada en
    test_planning_week.py: las tareas no están ancladas a un día (siguen
    "pendientes" hasta que se marcan a mano), así que "completada" es el
    estado de hoy de la tarea, no una confirmación de que se terminó justo
    el día en que este bloque se generó. Es la única señal real que existe
    hoy — no hay un timestamp de finalización por bloque en ningún lado, y
    no se inventa uno.

    Solo cuenta bloques de días ANTERIORES a `target_date` (el día de hoy
    todavía puede cambiar de estado en cualquier momento) y bloques cuya
    etiqueta quedó guardada — los planes generados antes de esa migración
    tienen `matched_preference_label = NULL` y quedan fuera del conteo,
    nunca se estiman retroactivamente.
    """
    rows = (
        db.query(RecommendationExplanation.matched_preference_label, Task.status)
        .join(PlanBlock, RecommendationExplanation.plan_block_id == PlanBlock.id)
        .join(DayPlan, PlanBlock.day_plan_id == DayPlan.id)
        .join(Task, Task.id == PlanBlock.source_id)
        .filter(
            DayPlan.user_id == user.id,
            DayPlan.date < target_date,
            PlanBlock.source_type == BlockSourceType.TASK,
            RecommendationExplanation.matched_preference_label.isnot(None),
        )
        .all()
    )

    stats: dict[str, engine.LabelStats] = {}
    for label, status in rows:
        entry = stats.setdefault(label, engine.LabelStats(completed=0, total=0))
        entry.total += 1
        if status == TaskStatus.COMPLETADA:
            entry.completed += 1
    return stats


def compute_streak(db: Session, user: User, today: date_type) -> dict:
    """
    Racha de días consecutivos en los que el usuario generó un plan
    (`day_plans` tiene un registro para ese día — 'Optimizar mi día' o
    '¿Qué hago ahora?' cuando genera uno de una vez, ver `whats_next`).
    Real, calculada de `day_plans.date`, no un contador simulado en el
    cliente.

    Si hoy todavía no tiene plan, la racha no se corta por eso solo —
    se cuenta desde ayer hacia atrás, para no castigar a alguien que
    simplemente no ha abierto la app todavía hoy. Si falta el día de
    ayer también, la racha es 0.
    """
    plan_dates = {
        row[0]
        for row in db.query(DayPlan.date).filter(DayPlan.user_id == user.id, DayPlan.date <= today).all()
    }

    has_plan_today = today in plan_dates
    cursor = today if has_plan_today else today - timedelta(days=1)

    streak = 0
    while cursor in plan_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return {"current_streak": streak, "has_plan_today": has_plan_today}


def whats_next(db: Session, user: User, now: datetime) -> dict:
    """
    '¿Qué hago ahora?' (sección 18 del brief). Si no hay plan generado para
    hoy, lo genera y lo guarda primero — el usuario no debería tener que
    saber que necesita optimizar antes de preguntar esto.
    """
    today = now.date()
    plan = get_plan(db, user, today)
    if plan is None:
        result = generate_plan(db, user, today)
        plan = persist_plan(db, user, today, result)

    blocks = sorted(plan.blocks, key=lambda b: b.start)

    current = next((b for b in blocks if b.start <= now < b.end), None)
    if current:
        return {
            "situation": "en_curso",
            "message": f"Ahora toca: {current.title} (hasta las {current.end.strftime('%H:%M')}).",
            "block_id": current.id,
        }

    upcoming = next((b for b in blocks if b.start > now), None)
    pending, _ = _build_task_items(db, user)
    scheduled_task_ids = {b.source_id for b in blocks if b.source_type == BlockSourceType.TASK}
    candidates = sorted(
        [t for t in pending if t.id not in scheduled_task_ids],
        key=lambda t: engine.urgency_score(t, today),
    )

    if upcoming is None:
        if candidates:
            best = candidates[0]
            return {
                "situation": "dia_libre",
                "message": (
                    f"No tienes más bloques planificados hoy. Con tu tiempo libre, te recomiendo avanzar en "
                    f"'{best.title}' ({best.duration_min} min, prioridad {best.priority})."
                ),
                "block_id": None,
            }
        return {
            "situation": "dia_libre",
            "message": (
                "No tienes más bloques planificados hoy y no te quedan tareas pendientes sin programar. "
                "Buen momento para descansar."
            ),
            "block_id": None,
        }

    gap_min = int((upcoming.start - now).total_seconds() // 60)
    fits = [t for t in candidates if t.duration_min <= gap_min]
    if fits and gap_min >= 10:
        best = fits[0]
        return {
            "situation": "hueco_libre",
            "message": (
                f"Tienes {gap_min} minutos libres antes de '{upcoming.title}'. Te recomiendo avanzar en "
                f"'{best.title}' ({best.duration_min} min)."
            ),
            "block_id": None,
        }

    return {
        "situation": "hueco_libre",
        "message": f"Tu siguiente actividad es '{upcoming.title}' en {gap_min} minutos.",
        "block_id": None,
    }
