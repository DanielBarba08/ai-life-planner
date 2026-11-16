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

    Hasta el 12 nov existía además un modelo "Objetivo" (Goal) separado,
    más ligero, con check-in diario manual. Daniel pidió eliminarlo
    ("siento que es similar a los hábitos") y fusionarlo aquí — un hábito
    ya cubre esa misma necesidad (meta recurrente + progreso real) y de
    sobra, así que `Habit` es ahora el único lugar para "quiero hacer algo
    de forma recurrente" en toda la app (ver migración
    2f19006119ec_elimina_objetivos_*.py).

    Las sesiones concretas de una semana se PROPONEN
    (`app/habits/service.py::suggest_sessions`) y se confirman
    automáticamente cada semana para cualquier hábito activo
    (`auto_confirm_due_sessions`, pedido por Daniel el 12 nov: "que se
    agreguen al horario" sin tener que entrar a Hábitos a confirmar a
    mano) — siguen sin inventar un día: se reparten con el mismo criterio
    de siempre (`suggest_sessions`), solo que ya no esperan a que el
    usuario dispare la confirmación.
    """

    __tablename__ = "habits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
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
