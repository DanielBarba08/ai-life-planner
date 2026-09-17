"""
Despacha una Intent (ver intents.py) contra los servicios reales del
Módulo 2 (goals) y del Módulo 3 (planning) — nunca contra datos
inventados. Esta es la pieza que hace cierto el punto 16 del brief: "La
IA debe utilizar los datos reales de la aplicación. NO debe responder
únicamente con texto genérico."
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.assistant import parser
from app.assistant.intents import Intent
from app.models.day_plan import DayPlan
from app.models.goal import Goal
from app.models.user import User
from app.planning import service as planning_service

EXAMPLES_HELP = (
    "Todavía no entiendo ese mensaje. Hoy puedo ayudarte con cosas como: "
    "\"¿qué hago ahora?\", \"organiza mi tarde\", \"reorganiza mi día\", "
    "\"optimiza mi día\", \"no terminé las tareas de ayer\", o "
    "\"quiero entrenar tres veces esta semana\"."
)


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
        return {"action": intent.action, "reply": result["message"], "day_plan": None, "goal": None}

    if intent.action == "optimize_day":
        result = planning_service.generate_plan(db, user, intent.target_date)
        day_plan = planning_service.persist_plan(db, user, intent.target_date, result)
        reply = f"Listo, armé tu día: {_format_plan_summary(day_plan)}."
        return {"action": intent.action, "reply": reply, "day_plan": day_plan, "goal": None}

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
        return {"action": intent.action, "reply": reply, "day_plan": day_plan, "goal": None}

    if intent.action == "create_goal":
        goal = Goal(
            user_id=user.id,
            title=intent.goal_title,
            horizon=intent.goal_horizon,
            confirmed_by_user=True,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        reply = (
            f"Agregué el objetivo \"{goal.title}\" (horizonte: {intent.goal_horizon}). "
            "Todavía no lo divido en sesiones programadas automáticamente — puedes crear tareas concretas "
            "para él cuando quieras que aparezcan en tu día."
        )
        return {"action": intent.action, "reply": reply, "day_plan": None, "goal": goal}

    if intent.action == "clarify":
        reply = (
            "Entendí que tienes una fecha límite nueva, pero no adivino sola a qué tarea se refiere para no "
            "cambiar algo que no me pediste. ¿Puedes decirme el nombre exacto de la tarea? Mientras tanto, "
            "también puedes editar su fecha límite directamente desde la tarea."
        )
        return {"action": intent.action, "reply": reply, "day_plan": None, "goal": None}

    return {"action": "unrecognized", "reply": EXAMPLES_HELP, "day_plan": None, "goal": None}
