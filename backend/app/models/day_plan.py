import enum
import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BlockSourceType(str, enum.Enum):
    EVENT = "event"
    TASK = "task"


class ConfidenceLevel(str, enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class DayPlan(Base):
    """
    Sección E: day_plans. Un registro por usuario y día — 'Optimizar mi
    día' y 'Replanificar' reemplazan/actualizan este registro, nunca
    crean uno nuevo para la misma fecha (así siempre hay un único plan
    vigente por día, como pide la sección 6 del brief: "Mi día").
    """

    __tablename__ = "day_plans"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_day_plans_user_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)

    total_available_min: Mapped[int] = mapped_column(Integer, default=0)
    total_requested_min: Mapped[int] = mapped_column(Integer, default=0)

    # Listas de dicts — ver DayPlanResult.unplaced / .conflicts en
    # app/planning/engine.py. No son entidades normalizadas porque son
    # metadatos de UNA generación del plan, no datos que se consulten por
    # separado (sección G del blueprint: "elementos sin ubicar, lista de
    # conflictos" son parte del DayPlan, no tablas propias).
    unplaced: Mapped[list] = mapped_column(JSON, default=list)
    conflicts: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blocks: Mapped[list["PlanBlock"]] = relationship(
        back_populates="day_plan", cascade="all, delete-orphan", order_by="PlanBlock.start"
    )


class PlanBlock(Base):
    """Sección E: plan_blocks."""

    __tablename__ = "plan_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    day_plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("day_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )

    source_type: Mapped[BlockSourceType] = mapped_column(Enum(BlockSourceType), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_movable: Mapped[bool] = mapped_column(default=True)

    day_plan: Mapped["DayPlan"] = relationship(back_populates="blocks")
    explanation: Mapped["RecommendationExplanation | None"] = relationship(
        back_populates="plan_block", uselist=False, cascade="all, delete-orphan"
    )


class RecommendationExplanation(Base):
    """
    Sección E: recommendation_explanations. Separa siempre datos del
    usuario / reglas del sistema / evidencia científica / inferencias de
    IA (sección 12 del brief). `evidence_ref_id` es un FK real hacia
    evidence_sources (Evidence Engine, sección F) desde que ese catálogo
    existe: sigue nulo salvo cuando el bloque cae en una ventana preferida
    (concentración/estudio/entrenamiento) para la que hay una cita
    verificada — nunca se inventa una referencia (sección 11 del brief).
    """

    __tablename__ = "recommendation_explanations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_block_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("plan_blocks.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    user_data_snippet: Mapped[str] = mapped_column(String(500), nullable=False)
    system_rule_snippet: Mapped[str] = mapped_column(String(500), nullable=False)
    evidence_ref_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True
    )
    ai_inference_snippet: Mapped[str] = mapped_column(String(500), nullable=False)
    confidence: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel), default=ConfidenceLevel.BAJA)
    # Personal Productivity Model (Fase 3 del roadmap): "concentración" |
    # "estudio" | "entrenamiento" | None — la misma etiqueta que ya
    # calculaba el motor (ver engine.py::_preference_label) pero que antes
    # se descartaba después de resolver evidence_ref_id. Se persiste desde
    # esta columna en adelante para poder calcular, más tarde, cuántos
    # bloques colocados en cada ventana preferida terminaron en una tarea
    # completada (service.py::compute_personal_stats). Los planes generados
    # ANTES de esta columna quedan en NULL — no se estima retroactivamente.
    matched_preference_label: Mapped[str | None] = mapped_column(String(20), nullable=True)

    plan_block: Mapped["PlanBlock"] = relationship(back_populates="explanation")
    evidence: Mapped["EvidenceSource | None"] = relationship()
