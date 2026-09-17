"""
Intérprete de intención real, con Claude y tool use — sustituye
`parser._parse_rule_based` (ver parser.py) cuando hay una
`ANTHROPIC_API_KEY` configurada. Esta es la pieza que el comentario
original de parser.py anticipaba: "cuando el usuario tenga una API key,
sustituir esta pieza por una que llame a Claude con tool use es un cambio
aislado a este archivo — no toca el router, el service, ni el Planning
Engine". Sigue siendo cierto: `classify_intent` devuelve el mismo
`Intent` que ya consume `app/assistant/service.py`, así que nada más
cambió.

Por qué tool use forzado y no dejar que Claude conteste con texto libre:
la salida tiene que mapear 1:1 al mismo contrato `Intent` que ya
consumen router/service/Planning Engine — un `tool_choice` forzado a un
solo tool es la única forma de garantizar una respuesta estructurada y
parseable siempre, sin depender de que el modelo "recuerde" devolver
JSON válido.

Por qué el LLM solo clasifica intención y no redacta la respuesta final:
decisión explícita para mantener acotado el cambio (ver docstring de
parser.py) — la respuesta al usuario en `service.py` ya está armada con
datos reales del plan/objetivo (sección 16 del brief: "la IA debe
utilizar los datos reales de la aplicación"), así que dejar que el LLM
solo decida "qué acción hacer" y no "qué texto inventar" mantiene esa
garantía sin tocar esa pieza ya verificada.
"""
from __future__ import annotations

from datetime import date as date_type

import anthropic

from app.assistant.intents import Intent
from app.config import get_settings

_SYSTEM_TEMPLATE = """Eres el clasificador de intención del asistente conversacional de AI Life Planner, una app de productividad personal. Tu único trabajo es clasificar el mensaje del usuario en UNA de seis acciones, usando la herramienta classify_intent — nunca respondas con texto libre, nunca inventes datos (tareas, títulos, fechas) que el usuario no mencionó.

Las seis acciones:

- whats_next: el usuario pregunta qué debería hacer ahora mismo o a continuación, sin pedir que se cambie nada del plan. Ej: "¿qué hago ahora?", "¿qué sigue?", "dime qué toca".
- optimize_day: el usuario pide que se arme/genere su plan del día por primera vez (aún no tiene uno, o quiere uno completamente nuevo desde cero). Ej: "optimiza mi día", "arma mi agenda de hoy", "planifica mi día".
- replan_day: el usuario quiere REORGANIZAR lo que ya está planeado o lo que queda del día — no un plan nuevo desde cero, sino ajustar el resto de hoy. Dispara con: (a) pedir reorganizar/reprogramar el día, la tarde, la mañana o la agenda ("reorganiza mi tarde", "reprograma lo que me queda"); (b) mencionar tareas que no terminó en un día anterior ("no terminé las tareas de ayer", "no acabé el proyecto"); (c) expresar cansancio/fatiga/agotamiento y pedir (implícita o explícitamente) que se ajuste lo que queda del día en torno a eso.
- create_goal: el usuario expresa el deseo de empezar a hacer algo de forma recurrente o con un horizonte de tiempo, típicamente empezando con "quiero" + un verbo de actividad (entrenar, estudiar, leer, aprender, meditar, correr, practicar, etc.). Ej: "quiero entrenar tres veces esta semana", "quiero leer más este mes".
- clarify: el usuario menciona una fecha límite o cambio sobre una tarea existente pero NO identifica cuál tarea por su nombre — nunca adivines a qué tarea se refiere. Ej: "tengo que terminar este proyecto mañana" (sin decir cuál proyecto/tarea).
- unrecognized: cualquier otro mensaje que no encaje claramente en las anteriores, incluyendo temas no relacionados con productividad/planificación (chistes, charla casual, preguntas generales).

Reglas para los campos de la herramienta:
- `note`: SOLO cuando action=replan_day. Usa "fatiga" si el usuario menciona estar cansado/agotado/sin energía/exhausto. Usa "tareas_previas_incompletas" si menciona tareas sin terminar de un día anterior. Omite el campo si ninguna aplica.
- `goal_title`: SOLO cuando action=create_goal. El título del objetivo tal como lo expresó el usuario, capitalizado, sin punto final — nunca lo inventes ni cambies su significado.
- `goal_horizon`: SOLO cuando action=create_goal. "semana" si menciona "esta semana", "mes" si menciona "este mes", "hoy" si menciona "hoy", si no — "largo_plazo".

Hoy es {today}. No necesitas calcular fechas — el sistema ya resuelve "hoy" del lado del servidor."""

_TOOL = {
    "name": "classify_intent",
    "description": "Clasifica el mensaje del usuario en una de las seis acciones que el asistente puede realizar sobre datos reales del usuario.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["whats_next", "optimize_day", "replan_day", "create_goal", "clarify", "unrecognized"],
                "description": "La acción clasificada.",
            },
            "note": {
                "type": "string",
                "enum": ["fatiga", "tareas_previas_incompletas"],
                "description": "Solo si action=replan_day y aplica una de las dos señales. Omitir en cualquier otro caso.",
            },
            "goal_title": {
                "type": "string",
                "description": "Solo si action=create_goal: el título del objetivo tal como lo dijo el usuario.",
            },
            "goal_horizon": {
                "type": "string",
                "enum": ["hoy", "semana", "mes", "largo_plazo"],
                "description": "Solo si action=create_goal.",
            },
        },
        "required": ["action"],
    },
}


class LLMUnavailable(Exception):
    """Sin key configurada, o la llamada a la API falló (red, rate limit, respuesta
    inesperada) — señal para que parser.py caiga al motor basado en reglas en vez
    de romper el asistente por completo."""


def classify_intent(text: str, today: date_type) -> Intent:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise LLMUnavailable("ANTHROPIC_API_KEY no configurada")

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.assistant_llm_model,
            max_tokens=300,
            system=_SYSTEM_TEMPLATE.format(today=today.isoformat()),
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "classify_intent"},
            messages=[{"role": "user", "content": text}],
        )
        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is None:
            raise LLMUnavailable("Claude no devolvió una clasificación estructurada")
        data = tool_use.input
    except anthropic.APIError as exc:
        raise LLMUnavailable(f"Error de la API de Anthropic: {exc}") from exc

    action = data.get("action")
    if action not in (
        "whats_next",
        "optimize_day",
        "replan_day",
        "create_goal",
        "clarify",
        "unrecognized",
    ):
        raise LLMUnavailable(f"Acción fuera del contrato: {action!r}")

    # target_date siempre es hoy — el chat no soporta pedir un día distinto
    # todavía, así que no dejamos que el modelo lo calcule (fuente de
    # errores de fecha innecesaria); mismo criterio que el motor de reglas.
    target_date = today if action in ("optimize_day", "replan_day") else None

    return Intent(
        action=action,
        target_date=target_date,
        goal_title=data.get("goal_title") if action == "create_goal" else None,
        goal_horizon=data.get("goal_horizon") if action == "create_goal" else None,
        note=data.get("note") if action == "replan_day" else None,
    )
