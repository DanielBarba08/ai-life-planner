import enum
import uuid
from datetime import time

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AvailabilityType(str, enum.Enum):
    """Tipo de disponibilidad recurrente (sección 5 del brief original)."""

    WORK = "trabajo"
    SCHOOL = "escuela"
    PERSONAL = "personal"
    OTHER = "otro"


class AvailabilityBlock(Base):
    """
    Disponibilidad recurrente semanal (sección E: availability_blocks).

    day_of_week sigue la convención ISO: 0 = lunes ... 6 = domingo.
    Esta tabla NO representa eventos puntuales (eso es fixed_events, que
    llega en el Módulo 2 junto con tasks/goals) — aquí solo vive el patrón
    semanal que el Planning Engine usa como restricción de fondo.
    """

    __tablename__ = "availability_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    type: Mapped[AvailabilityType] = mapped_column(Enum(AvailabilityType), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-6
    start: Mapped[time] = mapped_column(Time, nullable=False)
    end: Mapped[time] = mapped_column(Time, nullable=False)
    recurring: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="availability_blocks")
