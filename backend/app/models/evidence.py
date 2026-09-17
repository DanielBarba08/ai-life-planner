import enum
import uuid

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EvidenceLevel(str, enum.Enum):
    """
    Nivel de evidencia de una entrada del catálogo — sección 11 del brief:
    la app separa siempre evidencia sólida / moderada / limitada, nunca
    presenta un estudio individual como si fuera un consenso científico.
    """

    SOLIDA = "solida"
    MODERADA = "moderada"
    LIMITADA = "limitada"


class EvidenceSource(Base):
    """
    Sección E del blueprint: evidence_sources. El "Evidence Engine" (capa 5,
    sección F) — catálogo curado y ESTÁTICO: no existe endpoint para que un
    usuario, el asistente o un LLM creen o editen filas aquí. Cada entrada
    se agrega a mano, con una cita real y verificable (ver la migración de
    datos semilla en alembic/versions/ — cada DOI fue confirmado contra
    Crossref antes de insertarse, no generado).

    `claim` describe honestamente lo que el estudio encontró — no lo que le
    convendría decir a la app — y `limitations` documenta hasta dónde llega
    esa evidencia (tamaño de muestra, tipo de tarea, población), para que
    nunca se presente como una verdad absoluta ni como un mandato médico.
    Esto es lo que permite que el panel "¿Por qué?" muestre citas
    verificables en vez de inventar respaldo científico (sección 11 del
    brief), y le da al usuario suficiente información (fuente, autores,
    año, DOI) para juzgar él mismo qué tan confiable es.
    """

    __tablename__ = "evidence_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Une esta entrada con el tipo de bloque que respalda — ver
    # app/planning/engine.py::_preference_label (concentracion / estudio /
    # entrenamiento) y app/planning/evidence.py para el mapeo.
    topic: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    claim: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(300), nullable=False)  # revista / publicación
    authors: Mapped[str] = mapped_column(String(300), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    study_type: Mapped[str] = mapped_column(String(120), nullable=False)
    doi: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence_level: Mapped[EvidenceLevel] = mapped_column(Enum(EvidenceLevel), nullable=False)
    limitations: Mapped[str] = mapped_column(Text, nullable=False)
