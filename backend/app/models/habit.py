import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.task import ConcentrationLevel


class HabitStatus(str, enum.Enum):
    ACTIVO = "activo"
    PAUSADO = "pausado"


class Habit(Base):
    """
    Hábito recurrente (Fase 5 del roadmap — "hábitos avanzados").

    Un hábito NUNCA coloca tareas en el calendario por sí mismo: solo
    describe la meta recurrente ("entrenar 3 veces por semana"). Las
    sesiones concretas de una semana se PROPONEN
    (`app/habits/service.py::suggest_week`) y solo se convierten en tareas
    reales de verdad cuando el usuario las confirma explícitamente
    (`confirm_week` → filas reales en `tasks`, nunca automático) — mismo
    principio que ya aplica a `Goal.confirmed_by_user` (punto 14 del
    brief: "NO debe crear objetivos arbitrarios sin confirmación del
    usuario"), extendido aquí a las sesiones que genera un hábito.

    `goal_id` es opcional: un hábito puede nacer de un objetivo existente
    (ej. el objetivo "Entrenar tres veces esta semana" del asistente,
    sección 16 del brief) o crearse directo desde Ajustes → Hábitos, sin
    pasar por un objetivo.
    """

    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("goals.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Cuántas sesiones por semana persigue el hábito — sección de diseño
    # "racha visible" pedida por Daniel usa el mismo lenguaje ("2 de 3 esta
    # semana") para hábitos que para el streak diario de "Mi día".
    target_frequency_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_est_min: Mapped[int] = mapped_column(Integer, nullable=False)
    concentration_level: Mapped[ConcentrationLevel] = mapped_column(
        Enum(ConcentrationLevel), default=ConcentrationLevel.MEDIA
    )
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[HabitStatus] = mapped_column(Enum(HabitStatus), default=HabitStatus.ACTIVO)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship()
    goal: Mapped["Goal | None"] = relationship()
