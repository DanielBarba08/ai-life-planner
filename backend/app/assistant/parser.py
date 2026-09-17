"""
Intérprete de intención del asistente — la mitad "NLU" de la capa 4 del
blueprint (sección F).

`parse()` (el punto de entrada real, usado por service.py) intenta
primero un intérprete con Claude real (`app/assistant/llm_client.py`,
tool use forzado contra el mismo contrato `Intent`) y, si no hay
`ANTHROPIC_API_KEY` configurada o la llamada falla por cualquier motivo
(red, rate limit, respuesta inesperada), cae automáticamente a
`parse_rule_based` — el motor basado en reglas que este módulo tenía
antes de tener una key real. Este fallback no es un vestigio: es la capa
de resiliencia que evita que el asistente completo se caiga solo porque
la API de Anthropic tuvo un hiccup, y es honesto con el principio de "no
inventar, no afirmar lo que no se verificó" (secciones 11 y 27 del
brief) — si el LLM no puede responder, nunca inventamos una clasificación
a partir de una excepción, simplemente usamos el motor determinista.

Por qué el motor de reglas sigue viviendo aquí en vez de borrarse ahora
que existe la key real: sigue siendo la ruta de prueba determinista del
asistente (ver tests/test_assistant_parser.py, que lo prueba
directamente) y el piso de funcionalidad garantizado sin depender de un
proveedor externo — el asistente nunca queda inutilizable solo porque
falta o falla la key.

Ver también el README del Módulo 4 para la lista completa de frases que
el motor de reglas reconoce y las que hoy devuelven una pregunta
aclaratoria en vez de adivinar.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date as date_type

from app.assistant import llm_client
from app.assistant.intents import Intent

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


_FATIGUE_WORDS = ("cansad", "agotad", "exhaust")
_GOAL_TRIGGER_WORDS = ("entrenar", "estudiar", "leer", "aprender", "meditar", "correr", "practicar")


def parse(text: str, today: date_type) -> Intent:
    try:
        return llm_client.classify_intent(text, today)
    except llm_client.LLMUnavailable as exc:
        logger.info("Asistente: cayendo al motor de reglas (%s)", exc)
        return parse_rule_based(text, today)


def parse_rule_based(text: str, today: date_type) -> Intent:
    raw = text.strip()
    norm = _normalize(raw)

    fatigue = any(w in norm for w in _FATIGUE_WORDS)

    # "¿Qué debería hacer ahora?" / "qué hago ahora" — sección 18
    if re.search(r"\bque\s+(deberia|debo|hago|puedo)\s+hacer\b", norm) or "que hago ahora" in norm:
        return Intent(action="whats_next")

    # "No terminé las tareas de ayer" / "no termine el proyecto" — esas
    # tareas siguen con status=pendiente, así que ya son candidatas
    # automáticas de hoy; lo único que hace falta es replanificar.
    if re.search(r"\bno\s+(termine|termino|acabe|acabo)\b", norm):
        return Intent(action="replan_day", target_date=today, note="tareas_previas_incompletas")

    # "Organiza mi tarde" / "reorganiza mi día, estoy muy cansado"
    if re.search(r"\b(organiza|reorganiza|reprograma)\b", norm) and re.search(
        r"\b(dia|tarde|manana|agenda|semana)\b", norm
    ):
        note = "fatiga" if fatigue else None
        return Intent(action="replan_day", target_date=today, note=note)

    # "Optimiza mi día" / "arma mi día" — sección 7
    if re.search(r"\b(optimiza|arma|planifica)\b.*\b(dia|agenda)\b", norm):
        return Intent(action="optimize_day", target_date=today)

    # "Quiero entrenar tres veces esta semana" / "quiero estudiar más" — sección 14.
    # El objetivo se crea con confirmed_by_user=True porque el propio
    # usuario lo está pidiendo explícitamente en este mensaje (no es el
    # sistema proponiendo algo por su cuenta).
    if norm.startswith("quiero ") and any(w in norm for w in _GOAL_TRIGGER_WORDS):
        if "esta semana" in norm:
            horizon = "semana"
        elif "este mes" in norm:
            horizon = "mes"
        elif "hoy" in norm:
            horizon = "hoy"
        else:
            horizon = "largo_plazo"
        title = raw[0].upper() + raw[1:]
        if title.endswith("."):
            title = title[:-1]
        return Intent(action="create_goal", goal_title=title, goal_horizon=horizon)

    # "Tengo que terminar este proyecto mañana" — declara una fecha límite
    # sobre una tarea existente, pero adivinar CUÁL tarea (por texto
    # libre) es exactamente el tipo de acción irreversible que el punto 4
    # del brief prohíbe hacer sin control del usuario ("la IA recomienda,
    # no impone"). Se pide confirmación en vez de adivinar.
    if re.search(r"\btengo que terminar\b|\bnecesito terminar\b", norm):
        when = "mañana" if "manana" in norm else ("hoy" if " hoy" in f" {norm}" else None)
        return Intent(action="clarify", note=f"deadline_sin_tarea_identificada:{when or 'sin_fecha'}")

    return Intent(action="unrecognized")
