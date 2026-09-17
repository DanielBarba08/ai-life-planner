"""
Planning Engine — sección G del blueprint.

Este módulo es deliberadamente independiente de FastAPI y de SQLAlchemy:
recibe estructuras de datos simples (dataclasses) y devuelve un DayPlanResult,
también simple. Eso es lo que permite probarlo con pytest normal, sin DB ni
HTTP, y es la garantía central del punto 28 del brief: el LLM (cuando exista,
Módulo 4+) puede proponer una interpretación de lo que pide el usuario, pero
NUNCA genera la agenda directamente — solo este motor lo hace, y solo este
motor decide qué es factible.

Principios de diseño (ver también la sección 31 del brief):
  - Nunca comprime el sueño ni el descanso mínimo entre bloques.
  - Nunca "mete todo a la fuerza": si algo no cabe, se reporta como
    conflicto con una sugerencia concreta, no se fuerza en la agenda.
  - Toda decisión queda registrada en un `reasoning_trace` estructurado
    (no prosa) para que la capa de explicabilidad (sección F/12) lo pueda
    convertir en lenguaje natural sin inventar nada.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_type
from datetime import datetime, time, timedelta

PRIORITY_WEIGHT = {"alta": 3, "media": 2, "baja": 1}


# --------------------------------------------------------------------------
# Entradas
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime

    @property
    def duration_min(self) -> int:
        return int((self.end - self.start).total_seconds() // 60)

    def overlap(self, other: "TimeWindow") -> "TimeWindow | None":
        start = max(self.start, other.start)
        end = min(self.end, other.end)
        if start >= end:
            return None
        return TimeWindow(start, end)


@dataclass(frozen=True)
class FixedItem:
    """Un evento fijo o un bloque de disponibilidad recurrente — ambos son
    'ocupados' para el motor; ver README del Módulo 3 para la justificación
    de tratar ambos tipos igual."""

    id: str
    title: str
    start: datetime
    end: datetime


@dataclass(frozen=True)
class TaskItem:
    id: str
    title: str
    priority: str  # alta | media | baja
    duration_min: int
    concentration_level: str  # alta | media | baja
    category: str | None
    deadline: datetime | None
    depends_on_id: str | None


@dataclass(frozen=True)
class PreferenceWindows:
    """Rangos horarios preferidos, ya resueltos a `time` (no `datetime`) —
    el motor los combina con la fecha objetivo al planificar."""

    focus: list[tuple[time, time]] = field(default_factory=list)
    study: list[tuple[time, time]] = field(default_factory=list)
    workout: list[tuple[time, time]] = field(default_factory=list)
    min_break_min: int = 10


@dataclass
class LabelStats:
    """
    Personal Productivity Model (Fase 3 del roadmap) — historial REAL de
    finalización por ventana de preferencia ("concentración" | "estudio" |
    "entrenamiento"), calculado en service.py::compute_personal_stats a
    partir de `recommendation_explanations.matched_preference_label` (ver
    migración) cruzado con el estado actual de cada tarea. Este módulo
    solo recibe el resultado ya agregado — nunca toca la base de datos
    para calcularlo (ver docstring del archivo)."""

    completed: int
    total: int


# --------------------------------------------------------------------------
# Salidas
# --------------------------------------------------------------------------


@dataclass
class ReasoningTrace:
    user_data: str
    system_rule: str
    ai_inference: str
    confidence: str  # alta | media | baja — siempre "baja" hasta el Módulo 5 (PPM)
    # Campo estructurado (no prosa) que dice qué ventana de preferencia se usó
    # de verdad para colocar el bloque — "concentración" | "estudio" |
    # "entrenamiento" | None. Es lo que permite que la capa de explicabilidad
    # (app/planning/evidence.py) busque una cita real en vez de tener que
    # adivinarla parseando el texto de system_rule.
    matched_preference_label: str | None = None
    # Solo se usa al reconstruir bloques ya bloqueados en una replanificación
    # (ver service.py::generate_replan): conserva el evidence_ref_id que ya
    # tenía guardado ese bloque, en vez de tener que volver a resolverlo por
    # etiqueta (que no se guarda tal cual en la base de datos).
    evidence_ref_id: str | None = None


@dataclass
class PlannedBlock:
    source_type: str  # "event" | "task"
    source_id: str
    title: str
    start: datetime
    end: datetime
    is_movable: bool
    reasoning: ReasoningTrace | None = None


@dataclass
class UnplacedTask:
    task_id: str
    title: str
    duration_min: int
    reason: str
    suggestion: str


@dataclass
class Conflict:
    message: str
    suggestion: str


@dataclass
class DayPlanResult:
    date: date_type
    blocks: list[PlannedBlock]
    unplaced: list[UnplacedTask]
    conflicts: list[Conflict]
    total_available_min: int
    total_requested_min: int


# --------------------------------------------------------------------------
# Utilidades internas
# --------------------------------------------------------------------------


def _subtract_busy(window: TimeWindow, busy: list[TimeWindow]) -> list[TimeWindow]:
    """Resta una lista de intervalos ocupados de una ventana libre."""
    free = [window]
    for b in sorted(busy, key=lambda w: w.start):
        next_free: list[TimeWindow] = []
        for w in free:
            ov = w.overlap(b)
            if ov is None:
                next_free.append(w)
                continue
            if w.start < ov.start:
                next_free.append(TimeWindow(w.start, ov.start))
            if ov.end < w.end:
                next_free.append(TimeWindow(ov.end, w.end))
        free = next_free
    return [w for w in free if w.duration_min > 0]


def _preference_label(task: TaskItem) -> str | None:
    category = (task.category or "").strip().lower()
    if "estudi" in category:
        return "estudio"
    if "entren" in category or "ejercicio" in category or "gym" in category:
        return "entrenamiento"
    if task.concentration_level == "alta":
        return "concentración"
    return None


def _preferred_ranges_for(task: TaskItem, prefs: PreferenceWindows, target_date: date_type) -> list[TimeWindow]:
    label = _preference_label(task)
    raw = {"estudio": prefs.study, "entrenamiento": prefs.workout, "concentración": prefs.focus}.get(label, [])
    return [TimeWindow(datetime.combine(target_date, s), datetime.combine(target_date, e)) for s, e in raw]


PPM_MIN_SAMPLE = 5  # bloques mínimos con la misma etiqueta antes de hablar con más confianza


def _personal_model_inference(label: str | None, stats: dict[str, LabelStats] | None) -> tuple[str, str]:
    """
    Personal Productivity Model: traduce el historial real de finalización
    (agregado por service.py::compute_personal_stats, jamás aquí) en el
    texto de `ai_inference` y el `confidence` de un bloque. La única señal
    que existe hoy es "¿se completó la tarea que coloqué antes en esta
    ventana preferida?" — no hay duración real registrada en ningún lado
    todavía, así que este módulo no estima duraciones, solo confianza en
    la ventana elegida (sección 11 del brief: nunca inventar una señal que
    no existe).
    """
    if label is None:
        return (
            "No hay una ventana preferida configurada para este tipo de tarea (o ya estaba ocupada), "
            "así que todavía no aplica el análisis de historial personal.",
            "baja",
        )

    entry = (stats or {}).get(label)
    if entry is None or entry.total < PPM_MIN_SAMPLE:
        so_far = entry.total if entry else 0
        return (
            f"Todavía no tengo suficientes datos históricos tuyos en tu ventana de {label} "
            f"({so_far}/{PPM_MIN_SAMPLE} bloques registrados) — en cuanto acumules más, esta "
            "recomendación se volverá más precisa.",
            "baja",
        )

    rate = entry.completed / entry.total
    pct = round(rate * 100)
    if rate >= 0.7:
        return (
            f"De tus últimas {entry.total} tareas colocadas en tu ventana preferida de {label}, "
            f"completaste {entry.completed} ({pct}%). Por eso tengo más confianza en que este "
            "horario te funciona.",
            "alta",
        )
    if rate >= 0.4:
        return (
            f"De tus últimas {entry.total} tareas colocadas en tu ventana preferida de {label}, "
            f"completaste {entry.completed} ({pct}%) — un resultado mixto, así que la confianza en "
            "esta recomendación es media.",
            "media",
        )
    return (
        f"De tus últimas {entry.total} tareas colocadas en tu ventana preferida de {label}, solo "
        f"completaste {entry.completed} ({pct}%) — puede que esta ventana no te esté funcionando tan "
        "bien como pensábamos; considera ajustarla en Ajustes.",
        "baja",
    )


def urgency_score(task: TaskItem, target_date: date_type) -> tuple:
    score = PRIORITY_WEIGHT.get(task.priority, 2) * 10
    if task.deadline is not None:
        days_left = (task.deadline.date() - target_date).days
        if days_left <= 0:
            score += 15
        elif days_left <= 3:
            score += 8
        elif days_left <= 7:
            score += 4
    # Orden: mayor urgencia primero; a igual urgencia, tareas más cortas
    # primero (ayuda a que quepan más cosas); a igual duración, alfabético
    # para que el resultado sea determinista y testeable.
    return (-score, task.duration_min, task.title)


def _find_slot(
    duration_min: int,
    free_windows: list[TimeWindow],
    preferred: list[TimeWindow],
) -> TimeWindow | None:
    """Busca el mejor hueco: primero dentro de una ventana preferida, si
    existe y alcanza; si no, el primer hueco libre suficientemente largo."""
    needed = timedelta(minutes=duration_min)

    if preferred:
        candidates = []
        for free in free_windows:
            for pref in preferred:
                ov = free.overlap(pref)
                if ov and ov.duration_min >= duration_min:
                    candidates.append(TimeWindow(ov.start, ov.start + needed))
        if candidates:
            candidates.sort(key=lambda w: w.start)
            return candidates[0]

    fallback = [w for w in free_windows if w.duration_min >= duration_min]
    if not fallback:
        return None
    fallback.sort(key=lambda w: w.start)
    chosen = fallback[0]
    return TimeWindow(chosen.start, chosen.start + needed)


def _carve(free_windows: list[TimeWindow], placed: TimeWindow, buffer_min: int) -> list[TimeWindow]:
    """Quita el bloque recién colocado (más un colchón de descanso después)
    de la lista de ventanas libres."""
    occupied = TimeWindow(placed.start, placed.end + timedelta(minutes=buffer_min))
    result: list[TimeWindow] = []
    for w in free_windows:
        ov = w.overlap(occupied)
        if ov is None:
            result.append(w)
            continue
        if w.start < ov.start:
            result.append(TimeWindow(w.start, ov.start))
        if ov.end < w.end:
            result.append(TimeWindow(ov.end, w.end))
    return [w for w in result if w.duration_min > 0]


# --------------------------------------------------------------------------
# Punto de entrada
# --------------------------------------------------------------------------


def build_day_plan(
    *,
    target_date: date_type,
    wake_time: time,
    sleep_time: time,
    fixed_items: list[FixedItem],
    tasks: list[TaskItem],
    pending_task_ids: set[str],
    preferences: PreferenceWindows,
    locked_blocks: list[PlannedBlock] | None = None,
    min_start: datetime | None = None,
    personal_stats: dict[str, LabelStats] | None = None,
) -> DayPlanResult:
    """
    Construye (o reconstruye parcialmente, si se pasa `min_start`) el plan
    de un día. `locked_blocks` son bloques que ya no se tocan — vienen de
    una planificación anterior y ya pasaron o están en curso (ver Módulo 3
    README: replanificación nunca reoptimiza el día completo).
    """
    locked_blocks = locked_blocks or []

    day_start = datetime.combine(target_date, wake_time)
    day_end = datetime.combine(target_date, sleep_time)
    if day_end <= day_start:
        # Duerme después de medianoche del día siguiente: fuera de alcance
        # del MVP (ver limitaciones en el README) — tratamos el día como
        # vacío en vez de calcular horarios incorrectos.
        day_end = day_start

    window_start = max(day_start, min_start) if min_start else day_start
    whole_day = TimeWindow(window_start, day_end)

    busy = [TimeWindow(max(f.start, window_start), min(f.end, day_end)) for f in fixed_items]
    busy = [w for w in busy if w.duration_min > 0]
    busy += [TimeWindow(max(b.start, window_start), min(b.end, day_end)) for b in locked_blocks]
    busy = [w for w in busy if w.duration_min > 0]

    free_windows = _subtract_busy(whole_day, busy) if whole_day.duration_min > 0 else []
    total_available_min = sum(w.duration_min for w in free_windows)

    blocks: list[PlannedBlock] = [
        PlannedBlock("event", f.id, f.title, f.start, f.end, is_movable=False) for f in fixed_items
    ]
    blocks += [
        PlannedBlock(b.source_type, b.source_id, b.title, b.start, b.end, is_movable=False, reasoning=b.reasoning)
        for b in locked_blocks
    ]

    unplaced: list[UnplacedTask] = []
    schedulable = [t for t in tasks if t.id in pending_task_ids]
    total_requested_min = sum(t.duration_min for t in schedulable)

    for task in sorted(schedulable, key=lambda t: urgency_score(t, target_date)):
        if task.depends_on_id and task.depends_on_id in pending_task_ids:
            unplaced.append(
                UnplacedTask(
                    task_id=task.id,
                    title=task.title,
                    duration_min=task.duration_min,
                    reason="depende de otra tarea que todavía no está completada",
                    suggestion=f"Completa primero la tarea de la que depende '{task.title}'.",
                )
            )
            continue

        preferred = _preferred_ranges_for(task, preferences, target_date)
        slot = _find_slot(task.duration_min, free_windows, preferred)

        if slot is None:
            unplaced.append(
                UnplacedTask(
                    task_id=task.id,
                    title=task.title,
                    duration_min=task.duration_min,
                    reason="no hay un hueco disponible hoy de al menos esa duración",
                    suggestion=f"Recomiendo mover '{task.title}' a mañana o reducir su duración estimada.",
                )
            )
            continue

        matched_preference = bool(preferred) and any(slot.start >= p.start and slot.end <= p.end for p in preferred)
        label = _preference_label(task) if matched_preference else None
        ai_inference, confidence = _personal_model_inference(label, personal_stats)
        reasoning = ReasoningTrace(
            user_data=(
                f"Duración estimada: {task.duration_min} min · prioridad {task.priority} · "
                f"concentración {task.concentration_level}"
                + (f" · fecha límite {task.deadline.date().isoformat()}" if task.deadline else "")
            ),
            system_rule=(
                f"Colocada en tu ventana preferida de {_preference_label(task)} porque tienes disponibilidad ahí."
                if matched_preference
                else "Colocada en el primer hueco disponible con espacio suficiente, porque no hay una ventana "
                "preferida configurada para este tipo de tarea (o ya estaba ocupada)."
            ),
            ai_inference=ai_inference,
            confidence=confidence,
            matched_preference_label=label,
        )
        blocks.append(
            PlannedBlock("task", task.id, task.title, slot.start, slot.end, is_movable=True, reasoning=reasoning)
        )
        free_windows = _carve(free_windows, slot, preferences.min_break_min)

    conflicts: list[Conflict] = []
    if total_requested_min > total_available_min:
        conflicts.append(
            Conflict(
                message=(
                    f"Tienes {total_requested_min / 60:.1f} horas de tareas pendientes pero solo "
                    f"{total_available_min / 60:.1f} horas disponibles hoy."
                ),
                suggestion="Revisa las tareas marcadas como no ubicadas abajo — cada una trae una sugerencia concreta.",
            )
        )

    blocks.sort(key=lambda b: b.start)
    return DayPlanResult(
        date=target_date,
        blocks=blocks,
        unplaced=unplaced,
        conflicts=conflicts,
        total_available_min=total_available_min,
        total_requested_min=total_requested_min,
    )
