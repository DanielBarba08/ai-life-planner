"""
Pruebas de la capa de servicio (app/planning/service.py) enfocadas en el
Evidence Engine: que la evidencia real se resuelva al generar un plan, y
que un bloque bloqueado por una replanificación conserve su evidencia en
vez de perderla o tener que volver a resolverla.

Van directo contra la capa de servicio (no contra la API) porque necesitan
controlar `now` con precisión para forzar que un bloque quede "en el
pasado" — hacerlo a través de la API dependería del reloj real de la
máquina, lo que sería no determinista.
"""
from datetime import date, datetime, time

from app.models.preferences import UserPreferences
from app.models.task import ConcentrationLevel, Priority, Task
from app.models.user import User
from app.planning import service as planning_service

TARGET_DATE = date(2026, 9, 14)


def _make_user_with_focus_task(db):
    user = User(email="evidence@example.com", password_hash="x", wake_time=time(7, 0), sleep_time=time(23, 0))
    db.add(user)
    db.flush()
    db.add(
        UserPreferences(
            user_id=user.id,
            preferred_focus_hours=[{"start": "09:00", "end": "12:00"}],
        )
    )
    db.add(
        Task(
            user_id=user.id,
            title="Preparar presentación",
            duration_est_min=90,
            priority=Priority.ALTA,
            concentration_level=ConcentrationLevel.ALTA,
        )
    )
    db.commit()
    db.refresh(user)
    return user


def test_generate_plan_resolves_real_evidence_for_focus_window(db_session_factory):
    db = db_session_factory()
    user = _make_user_with_focus_task(db)

    result = planning_service.generate_plan(db, user, TARGET_DATE)
    day_plan = planning_service.persist_plan(db, user, TARGET_DATE, result)

    block = day_plan.blocks[0]
    assert block.explanation.evidence_ref_id is not None
    assert block.explanation.evidence.doi == "10.1037/0096-1523.27.4.763"
    db.close()


def test_locked_block_keeps_its_evidence_reference_through_a_replan(db_session_factory):
    db = db_session_factory()
    user = _make_user_with_focus_task(db)

    result = planning_service.generate_plan(db, user, TARGET_DATE)
    day_plan = planning_service.persist_plan(db, user, TARGET_DATE, result)
    original_evidence_id = day_plan.blocks[0].explanation.evidence_ref_id
    assert original_evidence_id is not None

    # 10:00 cae DESPUÉS de que el bloque de 09:00-10:30 ya empezó, así que
    # queda bloqueado tal cual por la replanificación (ver
    # service.py::generate_replan — solo bloquea bloques con start < now).
    now = datetime.combine(TARGET_DATE, time(10, 0))
    replanned = planning_service.generate_replan(db, user, TARGET_DATE, now)
    replanned_day_plan = planning_service.persist_plan(db, user, TARGET_DATE, replanned)

    locked_block = next(b for b in replanned_day_plan.blocks if b.title == "Preparar presentación")
    assert locked_block.explanation.evidence_ref_id == original_evidence_id
    db.close()
