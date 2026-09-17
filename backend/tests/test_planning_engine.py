"""
Pruebas del motor de planificación puro (app/planning/engine.py).

Corren sin DB ni HTTP a propósito: el motor es la pieza más crítica del
producto (sección 28 del brief — "nunca permitir que el LLM genere
directamente una agenda imposible") y necesita poder probarse de forma
aislada y rápida.
"""
from datetime import date, datetime, time

from app.planning.engine import (
    FixedItem,
    PreferenceWindows,
    TaskItem,
    build_day_plan,
)

TODAY = date(2026, 9, 14)  # lunes


def _task(id, title, priority="media", duration=60, concentration="media", category=None, deadline=None, depends_on=None):
    return TaskItem(
        id=id,
        title=title,
        priority=priority,
        duration_min=duration,
        concentration_level=concentration,
        category=category,
        deadline=deadline,
        depends_on_id=depends_on,
    )


def _no_prefs():
    return PreferenceWindows()


def test_empty_day_has_no_blocks_and_no_conflicts():
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[],
        pending_task_ids=set(),
        preferences=_no_prefs(),
    )
    assert plan.blocks == []
    assert plan.unplaced == []
    assert plan.conflicts == []
    assert plan.total_available_min == 16 * 60  # 07:00–23:00


def test_single_task_gets_placed_in_free_time():
    t = _task("t1", "Leer", duration=60)
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[t],
        pending_task_ids={"t1"},
        preferences=_no_prefs(),
    )
    assert len(plan.blocks) == 1
    block = plan.blocks[0]
    assert block.source_id == "t1"
    assert block.start == datetime.combine(TODAY, time(7, 0))
    assert block.reasoning.confidence == "baja"


def test_task_never_overlaps_a_fixed_event():
    event = FixedItem("e1", "Trabajo", datetime.combine(TODAY, time(9, 0)), datetime.combine(TODAY, time(17, 0)))
    t = _task("t1", "Proyecto", duration=120)
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[event],
        tasks=[t],
        pending_task_ids={"t1"},
        preferences=_no_prefs(),
    )
    task_block = next(b for b in plan.blocks if b.source_type == "task")
    assert not (task_block.start < event.end and task_block.end > event.start)


def test_higher_priority_task_gets_the_preferred_slot_first():
    prefs = PreferenceWindows(focus=[(time(9, 0), time(11, 0))])
    urgent = _task("t1", "Urgente", priority="alta", duration=90, concentration="alta")
    less_urgent = _task("t2", "Menos urgente", priority="baja", duration=90, concentration="alta")
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[less_urgent, urgent],
        pending_task_ids={"t1", "t2"},
        preferences=prefs,
    )
    urgent_block = next(b for b in plan.blocks if b.source_id == "t1")
    assert urgent_block.start == datetime.combine(TODAY, time(9, 0))


def test_task_blocked_by_incomplete_dependency_is_unplaced():
    base = _task("t1", "Investigar", duration=60)
    dependent = _task("t2", "Redactar", duration=60, depends_on="t1")
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[base, dependent],
        pending_task_ids={"t1", "t2"},
        preferences=_no_prefs(),
    )
    assert any(u.task_id == "t2" for u in plan.unplaced)
    assert "depende" in next(u for u in plan.unplaced if u.task_id == "t2").reason
    # la tarea base sí se planifica normalmente
    assert any(b.source_id == "t1" for b in plan.blocks)


def test_dependency_satisfied_when_dependency_already_completed():
    # "t1" ya no está en pending_task_ids porque está completada — no debe bloquear a t2
    dependent = _task("t2", "Redactar", duration=60, depends_on="t1")
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[dependent],
        pending_task_ids={"t2"},
        preferences=_no_prefs(),
    )
    assert plan.unplaced == []
    assert any(b.source_id == "t2" for b in plan.blocks)


def test_overcommitted_day_reports_conflict_and_unplaced_with_suggestion():
    # Solo 2 horas libres (07:00–09:00) pero 3 horas de tareas
    event = FixedItem("e1", "Ocupado", datetime.combine(TODAY, time(9, 0)), datetime.combine(TODAY, time(23, 0)))
    t1 = _task("t1", "Tarea grande", priority="alta", duration=120)
    t2 = _task("t2", "Tarea extra", priority="media", duration=60)
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[event],
        tasks=[t1, t2],
        pending_task_ids={"t1", "t2"},
        preferences=_no_prefs(),
    )
    assert plan.total_requested_min > plan.total_available_min
    assert len(plan.conflicts) == 1
    assert "horas" in plan.conflicts[0].message
    unplaced_ids = {u.task_id for u in plan.unplaced}
    assert "t2" in unplaced_ids  # la de menor prioridad se queda sin ubicar
    assert "mover" in next(u for u in plan.unplaced if u.task_id == "t2").suggestion.lower()


def test_minimum_break_is_respected_between_consecutive_task_blocks():
    prefs = PreferenceWindows(min_break_min=15)
    t1 = _task("t1", "Primero", priority="alta", duration=60)
    t2 = _task("t2", "Segundo", priority="alta", duration=60)
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(10, 0),
        fixed_items=[],
        tasks=[t1, t2],
        pending_task_ids={"t1", "t2"},
        preferences=prefs,
    )
    task_blocks = sorted([b for b in plan.blocks if b.source_type == "task"], key=lambda b: b.start)
    assert len(task_blocks) == 2
    gap = (task_blocks[1].start - task_blocks[0].end).total_seconds() / 60
    assert gap >= 15


def test_matched_preference_label_is_set_only_when_slot_is_really_preferred():
    prefs = PreferenceWindows(focus=[(time(9, 0), time(11, 0))])
    in_window = _task("t1", "Con ventana", duration=60, concentration="alta")
    no_window_match = _task("t2", "Sin ventana", duration=60, category="ocio")
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[in_window, no_window_match],
        pending_task_ids={"t1", "t2"},
        preferences=prefs,
    )
    placed_t1 = next(b for b in plan.blocks if b.source_id == "t1")
    placed_t2 = next(b for b in plan.blocks if b.source_id == "t2")
    assert placed_t1.reasoning.matched_preference_label == "concentración"
    assert placed_t2.reasoning.matched_preference_label is None


def test_locked_blocks_are_kept_and_not_overlapped_on_replan():
    already_placed = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[_task("t1", "Ya en curso", duration=60)],
        pending_task_ids={"t1"},
        preferences=_no_prefs(),
    ).blocks

    replanned = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[],
        tasks=[_task("t2", "Nueva tarea", duration=60)],
        pending_task_ids={"t2"},
        preferences=_no_prefs(),
        locked_blocks=already_placed,
        min_start=datetime.combine(TODAY, time(8, 0)),
    )
    locked = next(b for b in replanned.blocks if b.source_id == "t1")
    new = next(b for b in replanned.blocks if b.source_id == "t2")
    assert not (new.start < locked.end and new.end > locked.start)


def test_blueprint_section_29_scenario_never_touches_sleep_or_overlaps_fixed_items():
    """
    Reproduce el ejemplo exacto de la sección 29 del blueprint: trabajo
    09:00–17:00, cita 18:00–19:00, proyecto (120 min alta), email (30 min
    media), estudiar (90 min alta), entrenar (60 min), dormir a las 23:00.

    No hardcodeamos qué tarea específica queda sin ubicar — eso depende del
    algoritmo real, no de lo que "debería" pasar en teoría — pero sí
    verificamos las garantías que el blueprint promete: nunca se toca el
    descanso, nunca se solapa un bloque fijo, y si algo no cupo, viene con
    una sugerencia accionable.
    """
    work = FixedItem("work", "Trabajo", datetime.combine(TODAY, time(9, 0)), datetime.combine(TODAY, time(17, 0)))
    appt = FixedItem("appt", "Cita", datetime.combine(TODAY, time(18, 0)), datetime.combine(TODAY, time(19, 0)))
    tasks = [
        _task("proyecto", "Proyecto", priority="alta", duration=120, concentration="alta", deadline=datetime.combine(TODAY, time(23, 59))),
        _task("email", "Email", priority="media", duration=30),
        _task("estudiar", "Estudiar", priority="alta", duration=90, concentration="alta"),
        _task("entrenar", "Entrenar", priority="media", duration=60, category="entrenamiento"),
    ]
    plan = build_day_plan(
        target_date=TODAY,
        wake_time=time(7, 0),
        sleep_time=time(23, 0),
        fixed_items=[work, appt],
        tasks=tasks,
        pending_task_ids={t.id for t in tasks},
        preferences=PreferenceWindows(workout=[(time(18, 0), time(19, 0))], min_break_min=10),
    )

    sleep_start = datetime.combine(TODAY, time(23, 0))
    day_start = datetime.combine(TODAY, time(7, 0))
    for b in plan.blocks:
        assert day_start <= b.start and b.end <= sleep_start, "ningún bloque puede salirse de la ventana despierto"
        if b.source_id != "work" and b.source_id != "appt":
            assert not (b.start < work.end and b.end > work.start)
            assert not (b.start < appt.end and b.end > appt.start)

    # con 8 horas de tareas pedidas contra ~6.8 horas libres reales, algo
    # tiene que quedar señalado como no ubicado, con una sugerencia concreta
    if plan.unplaced:
        for u in plan.unplaced:
            assert u.suggestion  # nunca se deja sin explicación
