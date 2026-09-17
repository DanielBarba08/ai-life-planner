from datetime import datetime

from pydantic import BaseModel

from app.models.day_plan import ConfidenceLevel
from app.models.evidence import EvidenceLevel


class EvidenceRead(BaseModel):
    """
    Una entrada real del catálogo del Evidence Engine (sección F/E del
    blueprint) — nunca texto generado al momento. `doi` puede ser None si
    la fuente no tiene uno (poco común para estudios revisados por pares,
    pero el campo es opcional a propósito). El cliente puede resolver la
    cita completa en doi.org/{doi} para que el usuario la verifique él
    mismo, en vez de tener que confiar en la app.
    """

    claim: str
    source: str
    authors: str
    year: int
    study_type: str
    doi: str | None
    evidence_level: EvidenceLevel
    limitations: str


class ExplanationRead(BaseModel):
    """
    Respuesta de GET /v1/explanations/{block_id} — sección 12 del brief:
    siempre separa datos del usuario / reglas del sistema / evidencia
    científica / inferencias de IA en campos distintos, nunca mezclados en
    un solo párrafo.
    """

    block_id: str
    block_title: str
    block_start: datetime
    block_end: datetime

    user_data: str
    system_rule: str
    # None cuando el bloque no cayó en una ventana de preferencia con una
    # cita verificada en el catálogo (ver app/planning/evidence.py) — nunca
    # se rellena con una cita inventada para que el campo no quede vacío.
    evidence: EvidenceRead | None = None
    ai_inference: str
    confidence: ConfidenceLevel


class GeneralEvidenceRead(BaseModel):
    """
    Una fila de GET /v1/evidence/general — evidencia que respalda una regla
    GENERAL del motor (ej. "nunca comprimimos tu sueño"), no la colocación
    de un bloque específico. Mismo principio de separación que
    ExplanationRead: la regla y la evidencia van en campos distintos, nunca
    mezcladas en un párrafo.
    """

    topic: str
    system_rule: str
    evidence: EvidenceRead
