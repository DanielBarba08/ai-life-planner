"""
Segunda llamada a Claude que hace real la importación de horario
(action=import_schedule, ver app/assistant/intents.py). `classify_intent`
(app/assistant/llm_client.py) solo decide QUE el mensaje describe un
horario a importar — aquí es donde de verdad se extraen los bloques
concretos (tipo, días, horas, o fecha+hora si es un evento puntual), con
el mismo tool use forzado y el mismo principio de "nunca inventar" que ya
usa llm_client.py: si Claude no puede devolver una extracción válida
contra el contrato, no se inventa nada — se propaga `LLMUnavailable` (la
misma excepción de llm_client.py, reusada aquí a propósito para que
app/assistant/service.py maneje ambas llamadas con el mismo `except`) y
service.py le explica al usuario que esta función necesita Claude
configurado, en vez de fingir que entendió algo que no entendió.

Por qué es una llamada aparte de classify_intent y no el mismo tool:
extraer N bloques con datos concretos es una tarea distinta de clasificar
un mensaje en una de siete categorías fijas — mezclarlas en un solo
schema haría que classify_intent cargara con campos que casi nunca
aplican, y aquí hace falta un prompt específico (sobre todo para resolver
fechas relativas como "el viernes" contra la fecha de hoy, que
classify_intent ni siquiera necesita saber).

Por qué un bloque individual mal formado no tira toda la extracción: si
Claude entendió 4 de 5 bloques bien y uno vino con un campo inválido, es
mejor mostrarle al usuario los 4 que sí se pudieron leer (y que agregue
el quinto a mano) que descartar los cinco por uno solo.
"""
from __future__ import annotations

from datetime import date as date_type

import anthropic
from pydantic import ValidationError

from app.assistant.llm_client import LLMUnavailable
from app.config import get_settings
from app.schemas.assistant import ScheduleItem, ScheduleItemAvailability, ScheduleItemEvent

_DAY_NAMES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

_SYSTEM_TEMPLATE = """Eres el intérprete de importación de horario de AI Life Planner. El usuario te va a pegar o describir su horario en texto libre (compromisos recurrentes como trabajo, escuela, comidas, gimnasio, y/o eventos puntuales con fecha) y tu único trabajo es convertirlo en una lista estructurada de bloques, usando la herramienta extract_schedule — nunca inventes un bloque que el usuario no mencionó, y nunca inventes horas: si el usuario no da una hora para algo, no lo incluyas en la lista.

Cada bloque es uno de dos tipos:

- "availability": un compromiso RECURRENTE que se repite semana a semana en ciertos días. Usa `type` para clasificarlo: "trabajo", "escuela", "personal", "comida", "aseo" (bañarse/higiene), "descanso", u "otro" si no encaja en ninguno de los anteriores (ej. gimnasio, clases). Usa `days` con los días de la semana en los que ocurre (0=lunes, 1=martes, 2=miércoles, 3=jueves, 4=viernes, 5=sábado, 6=domingo) — "lunes a viernes" y "entre semana" son [0,1,2,3,4]; "fines de semana" es [5,6]; "todos los días" y "cada día" son los siete: [0,1,2,3,4,5,6].
- "event": algo puntual, en una fecha específica (no se repite cada semana). Usa `date` en formato YYYY-MM-DD, siempre resuelta a una fecha concreta — nunca dejes "el viernes" o "mañana" sin convertir. Hoy es {today} ({today_weekday}).

Para ambos tipos: `label` es un nombre corto tal como lo describiría el usuario (ej. "Trabajo", "Gimnasio", "Junta con el equipo"), y `start`/`end` son horas en formato HH:MM de 24 horas.

Si el mensaje no describe ningún bloque de horario reconocible (por ejemplo, es solo un saludo o una pregunta), regresa una lista vacía en `items` — no inventes contenido para rellenarla."""

_TOOL = {
    "name": "extract_schedule",
    "description": "Extrae la lista de bloques de horario (disponibilidad recurrente y/o eventos puntuales) descritos en el mensaje del usuario.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["availability", "event"]},
                        "label": {"type": "string", "description": "Nombre corto del bloque, tal como lo describió el usuario."},
                        "type": {
                            "type": "string",
                            "enum": ["trabajo", "escuela", "personal", "comida", "aseo", "descanso", "otro"],
                            "description": "Solo si kind=availability.",
                        },
                        "days": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Solo si kind=availability. 0=lunes...6=domingo.",
                        },
                        "date": {
                            "type": "string",
                            "description": "Solo si kind=event. Fecha YYYY-MM-DD ya resuelta, nunca relativa.",
                        },
                        "start": {"type": "string", "description": "Hora de inicio, HH:MM en formato 24 horas."},
                        "end": {"type": "string", "description": "Hora de fin, HH:MM en formato 24 horas."},
                    },
                    "required": ["kind", "label", "start", "end"],
                },
            },
        },
        "required": ["items"],
    },
}


def _parse_item(raw: dict) -> ScheduleItem:
    kind = raw.get("kind")
    if kind == "availability":
        return ScheduleItemAvailability(**raw)
    if kind == "event":
        return ScheduleItemEvent(**raw)
    raise ValueError(f"kind desconocido: {kind!r}")


def extract_schedule(text: str, today: date_type) -> list[ScheduleItem]:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise LLMUnavailable("ANTHROPIC_API_KEY no configurada")

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.assistant_llm_model,
            max_tokens=1500,
            system=_SYSTEM_TEMPLATE.format(today=today.isoformat(), today_weekday=_DAY_NAMES[today.weekday()]),
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "extract_schedule"},
            messages=[{"role": "user", "content": text}],
        )
        tool_use = next((b for b in response.content if b.type == "tool_use"), None)
        if tool_use is None:
            raise LLMUnavailable("Claude no devolvió una extracción estructurada")
        raw_items = tool_use.input.get("items", [])
    except anthropic.APIError as exc:
        raise LLMUnavailable(f"Error de la API de Anthropic: {exc}") from exc

    items: list[ScheduleItem] = []
    for raw in raw_items:
        try:
            items.append(_parse_item(raw))
        except (ValidationError, ValueError, TypeError):
            # Bloque individual mal formado — se descarta, no tira el resto
            # de la extracción (ver docstring del módulo).
            continue
    return items
