"""
Sección 16 del blueprint: 'el usuario puede decir... la IA debe utilizar
los datos reales de la aplicación'. Este archivo define la estructura
intermedia entre 'lo que el usuario escribió' y 'qué llamada real se hace
contra el Planning Engine' — el mismo contrato que usaría un intérprete
basado en un LLM (Fase LLM real, ver README del Módulo 4), así que
cambiar el intérprete de reglas por Claude más adelante no toca nada más
que app/assistant/parser.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from typing import Literal

IntentAction = Literal[
    "whats_next",
    "optimize_day",
    "replan_day",
    "create_habit",
    "import_schedule",
    "clarify",
    "unrecognized",
]


@dataclass(frozen=True)
class Intent:
    action: IntentAction
    target_date: date_type | None = None
    # Solo cuando action=create_habit — ver app/assistant/service.py. Si el
    # usuario no dio una frecuencia explícita ("tres veces", "todos los
    # días"), el parser nunca inventa una: devuelve action=clarify en vez
    # de esto (mismo principio de "nunca inventar" que ya aplica al resto
    # del asistente).
    habit_title: str | None = None
    habit_frequency_per_week: int | None = None
    note: str | None = None  # contexto detectado (ej. "cansado") que el service usa al redactar la respuesta
