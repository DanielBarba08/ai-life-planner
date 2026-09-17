"""
Puente entre el Planning Engine (que solo conoce el texto "concentración" /
"estudio" / "entrenamiento" que ya usa en sus explicaciones — ver
_preference_label en app/planning/engine.py) y el catálogo curado de
app/models/evidence.py. Deliberadamente NO vive dentro de engine.py: el
motor sigue sin saber que la base de datos existe (ver el docstring de
engine.py); esta capa de servicio es la única que traduce entre ambos.

Solo se adjunta evidencia cuando el bloque cayó realmente en la ventana
preferida correspondiente (`matched_preference` en engine.py) — un bloque
colocado por "primer hueco disponible" es una decisión heurística, no una
recomendación con respaldo científico, y decirlo de otra forma sería
inventar una conexión que no existe (sección 11 del brief).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evidence import EvidenceSource

# Mapea la etiqueta que ya usa el motor (español, con acentos, pensada para
# prosa) al `topic` ASCII con el que se guardan las filas en evidence_sources.
_LABEL_TO_TOPIC = {
    "concentración": "concentracion",
    "estudio": "estudio",
    "entrenamiento": "entrenamiento",
}


# Reglas GENERALES del motor (no la colocación de un bloque en particular)
# que ya tienen una cita real investigada y verificada — ver el comentario
# en app/planning/evidence_catalog.py sobre por qué viven separadas del
# mapeo de arriba. El texto es la regla tal cual la implementa el motor,
# escrito a mano (nunca generado), no una interpretación de lo que dice el
# estudio.
GENERAL_RULES: dict[str, str] = {
    "descanso": (
        "El motor siempre deja un colchón de descanso entre bloques de tareas (configurable en Ajustes → "
        "Preferencias, minutos mínimos entre bloques) — nunca encima una tarea justo después de otra."
    ),
    "sueno": (
        "El motor nunca planifica nada fuera de tu horario de despertar/dormir — tu ventana de sueño está "
        "siempre protegida, sin excepción, sin importar cuántas tareas tengas pendientes."
    ),
    "priorizacion": (
        "Al decidir qué tarea colocar primero cuando compiten varias, el motor combina tu prioridad "
        "(alta/media/baja) con qué tan cerca está la fecha límite — nunca ordena solo por cuál vence antes."
    ),
}


def list_general_evidence(db: Session) -> list[dict]:
    """
    Evidencia que respalda reglas generales del motor, no un bloque en
    particular — pensada para un lugar propio en la app (ej. "Cómo decide
    tus horarios" en Ajustes), separado del panel "¿Por qué?" de cada
    bloque. Si una regla en `GENERAL_RULES` todavía no tiene ninguna fila
    en el catálogo con ese `topic`, se omite en vez de mostrarse sin
    evidencia — mismo principio que el resto del Evidence Engine: nunca
    mostrar una sección vacía como si fuera evidencia inventada.
    """
    order = {"solida": 0, "moderada": 1, "limitada": 2}
    result: list[dict] = []
    for topic, system_rule in GENERAL_RULES.items():
        candidates = db.query(EvidenceSource).filter(EvidenceSource.topic == topic).all()
        if not candidates:
            continue
        candidates.sort(key=lambda e: order.get(e.evidence_level.value, 9))
        result.append({"topic": topic, "system_rule": system_rule, "evidence": candidates[0]})
    return result


def find_evidence_for_label(db: Session, label: str | None) -> EvidenceSource | None:
    """
    Devuelve la entrada del catálogo para esta etiqueta, si existe. Si hay
    más de una fuente para el mismo tema (no es el caso hoy, pero el
    catálogo puede crecer), se prioriza la de evidencia más sólida.
    """
    if label is None:
        return None
    topic = _LABEL_TO_TOPIC.get(label)
    if topic is None:
        return None

    order = {"solida": 0, "moderada": 1, "limitada": 2}
    candidates = db.query(EvidenceSource).filter(EvidenceSource.topic == topic).all()
    if not candidates:
        return None
    candidates.sort(key=lambda e: order.get(e.evidence_level.value, 9))
    return candidates[0]
