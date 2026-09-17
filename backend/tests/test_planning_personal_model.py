"""
Personal Productivity Model (Fase 3 del roadmap) — historial real de
finalización por ventana de preferencia. Van directo contra la capa de
servicio (igual que test_planning_evidence_service.py) porque necesitan
crear bloques en días específicos del PASADO y marcar tareas como
completadas a mano, sin depender del reloj real de la máquina.
"""
from datetime import date, time, timedelta

from app.models.preferences import UserPreferences
from app.models.task import ConcentrationLevel, Priority, Task, TaskStatus
from app.models.user import User
from app.planning import service as planning_service
from app.planning.engine import PPM_MIN_SAMPLE

TARGET_DATE = date(2026, 9, 20)


def _make_user(db):
    user = User(email="ppm@example.com", password_hash="x", wake_time=time(7, 0), sleep_time=time(23, 0))
    db.add(user)
    db.flush()
    db.add(UserPreferences(user_id=user.id, preferred_focus_hours=[{"start": "09:00", "end": "12:00"}]))
    db.commit()
    db.refresh(user)
    return user


def _plan_and_complete_focus_task(db, user, day: date, *, complete: bool):
    """Genera y guarda un plan para `day` con una sola tarea de concentración
    alta (cae en la ventana de foco de _make_user), y la marca como
    completada o pospuesta según `complete` — así queda un bloque histórico
    real con matched_preference_label='concentración' para que
    compute_personal_stats lo cuente. Se usa POSPUESTA (no dejarla
    "pendiente") para las que no se completan: una tarea pendiente seguiría
    apareciendo en los planes de los días siguientes (las tareas no están
    ancladas a un día — ver test_planning_week.py), lo que inflaría el
    conteo histórico de este mismo helper al llamarlo varias veces seguidas."""
    task = Task(
        user_id=user.id,
        title=f"Tarea foco {day.isoformat()}",
        duration_est_min=60,
        priority=Priority.MEDIA,
        concentration_level=ConcentrationLevel.ALTA,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    result = planning_service.generate_plan(db, user, day)
    day_plan = planning_service.persist_plan(db, user, day, result)
    assert day_plan.blocks[0].explanation.matched_preference_label == "concentración"

    task.status = TaskStatus.COMPLETADA if complete else TaskStatus.POSPUESTA
    db.commit()

    return day_plan


def _add_pending_focus_task(db, user, day: date) -> Task:
    """Agrega una tarea de concentración alta pendiente, SIN generar ni
    guardar un plan — para usarla como la tarea "de hoy" que sí queremos
    ver reflejada en el resultado de generate_plan(TARGET_DATE)."""
    task = Task(
        user_id=user.id,
        title=f"Tarea foco objetivo {day.isoformat()}",
        duration_est_min=60,
        priority=Priority.MEDIA,
        concentration_level=ConcentrationLevel.ALTA,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def test_matched_preference_label_is_persisted_on_the_explanation(db_session_factory):
    db = db_session_factory()
    user = _make_user(db)

    _plan_and_complete_focus_task(db, user, TARGET_DATE - timedelta(days=1), complete=True)
    db.close()


def test_stays_baja_confidence_below_the_minimum_sample(db_session_factory):
    db = db_session_factory()
    user = _make_user(db)

    # Menos de PPM_MIN_SAMPLE bloques históricos con la etiqueta.
    for i in range(PPM_MIN_SAMPLE - 1):
        _plan_and_complete_focus_task(db, user, TARGET_DATE - timedelta(days=i + 1), complete=True)

    _add_pending_focus_task(db, user, TARGET_DATE)
    result = planning_service.generate_plan(db, user, TARGET_DATE)
    block = next(b for b in result.blocks if b.reasoning is not None)
    assert block.reasoning.confidence == "baja"
    assert f"{PPM_MIN_SAMPLE - 1}/{PPM_MIN_SAMPLE}" in block.reasoning.ai_inference
    db.close()


def test_high_completion_rate_raises_confidence_to_alta(db_session_factory):
    db = db_session_factory()
    user = _make_user(db)

    for i in range(PPM_MIN_SAMPLE):
        _plan_and_complete_focus_task(db, user, TARGET_DATE - timedelta(days=i + 1), complete=True)

    _add_pending_focus_task(db, user, TARGET_DATE)
    result = planning_service.generate_plan(db, user, TARGET_DATE)
    block = next(b for b in result.blocks if b.reasoning is not None)
    assert block.reasoning.confidence == "alta"
    assert f"completaste {PPM_MIN_SAMPLE} ({100}%)" in block.reasoning.ai_inference
    db.close()


def test_low_completion_rate_keeps_confidence_baja_with_honest_explanation(db_session_factory):
    db = db_session_factory()
    user = _make_user(db)

    # 1 de PPM_MIN_SAMPLE completadas → 20% con PPM_MIN_SAMPLE=5.
    for i in range(PPM_MIN_SAMPLE):
        completed = i == 0
        _plan_and_complete_focus_task(db, user, TARGET_DATE - timedelta(days=i + 1), complete=completed)

    _add_pending_focus_task(db, user, TARGET_DATE)
    result = planning_service.generate_plan(db, user, TARGET_DATE)
    block = next(b for b in result.blocks if b.reasoning is not None)
    assert block.reasoning.confidence == "baja"
    assert "solo completaste 1" in block.reasoning.ai_inference
    db.close()


def test_only_counts_blocks_strictly_before_target_date(db_session_factory):
    db = db_session_factory()
    user = _make_user(db)

    for i in range(PPM_MIN_SAMPLE):
        _plan_and_complete_focus_task(db, user, TARGET_DATE - timedelta(days=i + 1), complete=True)

    stats_before = planning_service.compute_personal_stats(db, user, TARGET_DATE)
    assert stats_before["concentración"].total == PPM_MIN_SAMPLE

    # Un bloque persistido del mismo TARGET_DATE no debe contar como
    # historial de sí mismo (el día de hoy todavía puede cambiar de estado).
    _plan_and_complete_focus_task(db, user, TARGET_DATE, complete=True)
    stats_same_day = planning_service.compute_personal_stats(db, user, TARGET_DATE)
    assert stats_same_day["concentración"].total == PPM_MIN_SAMPLE

    # Pero consultado para el día siguiente, ese bloque ya es pasado y sí cuenta.
    stats_next_day = planning_service.compute_personal_stats(db, user, TARGET_DATE + timedelta(days=1))
    assert stats_next_day["concentración"].total == PPM_MIN_SAMPLE + 1
    db.close()


def test_unmatched_blocks_keep_the_static_no_window_message(db_session_factory):
    db = db_session_factory()
    user = User(email="ppm-nowindow@example.com", password_hash="x", wake_time=time(7, 0), sleep_time=time(23, 0))
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        Task(
            user_id=user.id,
            title="Tarea sin ventana preferida",
            duration_est_min=30,
            priority=Priority.MEDIA,
            concentration_level=ConcentrationLevel.BAJA,
        )
    )
    db.commit()

    result = planning_service.generate_plan(db, user, TARGET_DATE)
    block = next(b for b in result.blocks if b.reasoning is not None)
    assert block.reasoning.matched_preference_label is None
    assert block.reasoning.confidence == "baja"
    assert "no aplica el análisis de historial personal" in block.reasoning.ai_inference
    db.close()


def test_locked_block_through_a_replan_keeps_its_persisted_label(db_session_factory):
    from datetime import datetime

    db = db_session_factory()
    user = _make_user(db)

    task = Task(
        user_id=user.id,
        title="Preparar presentación",
        duration_est_min=90,
        priority=Priority.ALTA,
        concentration_level=ConcentrationLevel.ALTA,
    )
    db.add(task)
    db.commit()

    result = planning_service.generate_plan(db, user, TARGET_DATE)
    day_plan = planning_service.persist_plan(db, user, TARGET_DATE, result)
    assert day_plan.blocks[0].explanation.matched_preference_label == "concentración"

    now = datetime.combine(TARGET_DATE, time(10, 0))
    replanned = planning_service.generate_replan(db, user, TARGET_DATE, now)
    replanned_day_plan = planning_service.persist_plan(db, user, TARGET_DATE, replanned)

    locked_block = next(b for b in replanned_day_plan.blocks if b.title == "Preparar presentación")
    assert locked_block.explanation.matched_preference_label == "concentración"
    db.close()
