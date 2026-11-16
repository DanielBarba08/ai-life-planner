"""
Despacha una Intent (ver intents.py) contra los servicios reales del
Módulo 2 (hábitos) y del Módulo 3 (planning) — nunca contra datos
inventados. Esta es la pieza que hace cierto el punto 16 del brief: "La
IA debe utilizar los datos reales de la aplicación. NO debe responder
únicamente con texto genérico."
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.assistant import parser, schedule_extractor
from app.assistant.intents import Intent
from app.assistant.llm_client import LLMUnavailable
from app.habits import service as habits_service
from app.models.availability import AvailabilityBlock
from app.models.day_plan import DayPlan
from app.models.event import FixedEvent
from app.models.habit import Habit
from app.models.task import ConcentrationLevel
from app.models.user import User
from app.planning import service as planning_service
from app.schemas.assistant import ScheduleItem, ScheduleItemAvailability

EXAMPLES_HELP = (
    "Todavía no entiendo ese mensaje. Hoy puedo ayudarte con cosas como: "
    "\"¿qué hago ahora?\", \"organiza mi tarde\", \"reorganiza mi día\", "
    "\"optimiza mi día\", \"no terminé las tareas de ayer\", "
    "\"quiero entrenar tres veces esta semana\", o \"importa mi horario: ...\"."
)

# Duración y concentración por default cuando el asistente crea un
# hábito desde el chat (ej. "quiero entrenar tres veces esta semana") —
# el usuario nunca da esos dos datos en una frase así, así que en vez de
# bloquear la creación pidiéndolos uno por uno (lo que convertiría una
# sola frase en un interrogatorio), se usa un default razonable Y SE
# AVISA explícitamente en la respuesta (ver _format_habit_created) para
# que quede claro que es un valor editable, no un dato inventado en
# silencio — mismo espíritu del punto 14 del brief, aplicado a lo que de
# verdad hace falta para poder crear la fila.
_DEFAULT_HABIT_DURATION_MIN = 30
_DEFAULT_HABIT_CONCENTRATION = ConcentrationLevel.MEDIA

_WEEKDAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

IMPORT_SCHEDULE_NO_LLM_REPLY = (
    "Para importar un horario completo necesito que el servidor tenga configurada una API key de Claude — "
    "sin eso no puedo interpretar texto libre de forma confiable, y prefiero no inventar bloques a partir de una "
    "suposición. Mientras tanto puedes seguir agregando tus bloques a mano en Disponibilidad y Eventos."
)

IMPORT_SCHEDULE_EMPTY_REPLY = (
    "No logré identificar ningún bloque de horario en tu mensaje. Intenta describirlo con días y horas, por "
    "ejemplo: \"trabajo de 9 a 6 lunes a viernes, gimnasio martes y jueves 7pm\"."
)

_DAY_ABBR = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def _format_schedule_preview(items: list[ScheduleItem]) -> str:
    lines = []
    for item in items:
        rango = f"{item.start.strftime('%H:%M')}–{item.end.strftime('%H:%M')}"
        if isinstance(item, ScheduleItemAvailability):
            dias = ", ".join(_DAY_ABBR[d] for d in item.days)
            lines.append(f"• {item.label}: {dias} {rango}")
        else:
            lines.append(f"• {item.label}: {item.date.strftime('%d/%m')} {rango}")
    return "Esto es lo que entendí de tu horario:\n" + "\n".join(lines) + "\n\n¿Lo agrego tal cual?"


def _format_plan_summary(day_plan: DayPlan) -> str:
    task_blocks = [b for b in day_plan.blocks if b.source_type.value == "task"]
    parts = [f"quedaron {len(task_blocks)} tarea(s) planificada(s) hoy"]
    if day_plan.conflicts:
        parts.append(day_plan.conflicts[0]["message"])
    if day_plan.unplaced:
        nombres = ", ".join(u["title"] for u in day_plan.unplaced)
        parts.append(f"sin ubicar: {nombres}")
    return " · ".join(parts)


def handle_message(db: Session, user: User, text: str) -> dict:
    now = planning_service.local_now(user)
    today = now.date()
    intent: Intent = parser.parse(text, today)

    if intent.action == "whats_next":
        result = planning_service.whats_next(db, user, now)
        return {"action": intent.action, "reply": result["message"], "day_plan": None, "habit": None}

    if intent.action == "optimize_day":
        result = planning_service.generate_plan(db, user, intent.target_date)
        day_plan = planning_service.persist_plan(db, user, intent.target_date, result)
        reply = f"Listo, armé tu día: {_format_plan_summary(day_plan)}."
        return {"action": intent.action, "reply": reply, "day_plan": day_plan, "habit": None}

    if intent.action == "replan_day":
        result = planning_service.generate_replan(db, user, intent.target_date, now)
        day_plan = planning_service.persist_plan(db, user, intent.target_date, result)
        prefix = "Reorganicé lo que queda de tu día"
        if intent.note == "tareas_previas_incompletas":
            prefix = "Las tareas que no terminaste siguen pendientes — las acomodé en lo que queda de hoy"
        reply = f"{prefix}: {_format_plan_summary(day_plan)}."
        if intent.note == "fatiga":
            reply += (
                " Noté que mencionaste estar cansado: hoy todavía no ajusto la carga automáticamente "
                "según tu energía reportada (eso es una función de una fase futura), pero puedes editar "
                "o posponer cualquier bloque a mano."
            )
        return {"action": intent.action, "reply": reply, "day_plan": day_plan, "habit": None}

    if intent.action == "create_habit":
        habit = Habit(
            user_id=user.id,
            title=intent.habit_title,
            target_frequency_per_week=intent.habit_frequency_per_week,
            duration_est_min=_DEFAULT_HABIT_DURATION_MIN,
            concentration_level=_DEFAULT_HABIT_CONCENTRATION,
        )
        db.add(habit)
        db.commit()
        db.refresh(habit)

        # Lo agrega al calendario de esta semana de inmediato (no espera a
        # que el usuario abra Hábitos o Mi día — pedido por Daniel el 12
        # nov: "que se agreguen al horario") y avisa en qué días quedó,
        # para que la duración/concentración por default no quede
        # escondida: el usuario ve exactamente qué se creó y puede
        # ajustarla en Hábitos.
        created = habits_service.auto_confirm_due_sessions(db, user.id, today)
        this_habit_days = sorted(t.deadline.date() for t in created if t.habit_id == habit.id)
        dias_txt = ", ".join(_WEEKDAY_NAMES[d.weekday()] for d in this_habit_days)

        reply = (
            f"Agregué el hábito \"{habit.title}\" ({habit.target_frequency_per_week}x por semana, "
            f"{_DEFAULT_HABIT_DURATION_MIN} min por sesión — ajusta la duración o la concentración cuando "
            "quieras en Hábitos)."
        )
        if dias_txt:
            reply += f" Ya quedó en tu calendario esta semana: {dias_txt}."
        return {"action": intent.action, "reply": reply, "day_plan": None, "habit": habit}

    if intent.action == "import_schedule":
        try:
            items = schedule_extractor.extract_schedule(text, today)
        except LLMUnavailable:
            return {
                "action": intent.action,
                "reply": IMPORT_SCHEDULE_NO_LLM_REPLY,
                "day_plan": None,
                "habit": None,
                "pending_import": None,
            }
        if not items:
            return {
                "action": intent.action,
                "reply": IMPORT_SCHEDULE_EMPTY_REPLY,
                "day_plan": None,
                "habit": None,
                "pending_import": None,
            }
        return {
            "action": intent.action,
            "reply": _format_schedule_preview(items),
            "day_plan": None,
            "habit": None,
            "pending_import": items,
        }

    if intent.action == "clarify":
        if intent.note and intent.note.startswith("frecuencia_habito_sin_especificar:"):
            title = intent.note.split(":", 1)[1]
            reply = (
                f"Para agregar \"{title}\" como hábito necesito saber cuántas veces por semana — no quiero "
                "inventar un número que no dijiste. ¿Cuántas veces a la semana quieres hacerlo? (por ejemplo, "
                "\"tres veces\" o \"todos los días\")."
            )
        else:
            reply = (
                "Entendí que tienes una fecha límite nueva, pero no adivino sola a qué tarea se refiere para no "
                "cambiar algo que no me pediste. ¿Puedes decirme el nombre exacto de la tarea? Mientras tanto, "
                "también puedes editar su fecha límite directamente desde la tarea."
            )
        return {"action": intent.action, "reply": reply, "day_plan": None, "habit": None}

    return {"action": "unrecognized", "reply": EXAMPLES_HELP, "day_plan": None, "habit": None}


def import_schedule_items(db: Session, user: User, items: list[ScheduleItem]) -> dict:
    """
    Confirmación explícita de la vista previa de action=import_schedule —
    lo único que de verdad escribe en la base de datos (sección 4 del
    brief: "la IA recomienda, no impone"; handle_message solo propone).

    Cada ScheduleItemAvailability se expande a un AvailabilityBlock por
    día marcado en `days` — mismo criterio que ya usa el modal de
    Disponibilidad en el frontend (un POST por día, ver
    AvailabilityFormModal.tsx), solo que aquí la expansión ocurre del
    lado del servidor en una sola llamada. Los rangos start<end ya
    quedaron validados por el schema (ScheduleItemField) antes de llegar
    aquí, así que no hace falta repetir esa validación.
    """
    availability_created = 0
    events_created = 0
    for item in items:
        if isinstance(item, ScheduleItemAvailability):
            for day in item.days:
                db.add(
                    AvailabilityBlock(
                        user_id=user.id,
                        type=item.type,
                        day_of_week=day,
                        start=item.start,
                        end=item.end,
                    )
                )
                availability_created += 1
        else:
            db.add(
                FixedEvent(
                    user_id=user.id,
                    title=item.label,
                    start=datetime.combine(item.date, item.start),
                    end=datetime.combine(item.date, item.end),
                )
            )
            events_created += 1
    db.commit()
    return {"availability_created": availability_created, "events_created": events_created}
