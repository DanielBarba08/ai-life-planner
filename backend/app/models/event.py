import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventSource(str, enum.Enum):
    """De dónde vino el evento (sección E: fixed_events.source)."""

    MANUAL = "manual"
    EXTERNAL_CALENDAR = "calendario_externo"  # reservado para la fase 6 (integraciones)


class FixedEvent(Base):
    """
    Evento fijo del calendario (sección E: fixed_events).

    A diferencia de una tarea, un evento tiene horario propio y el Planning
    Engine (Módulo 3) lo trata siempre como inamovible: nunca se reprograma
    automáticamente, solo el usuario puede editarlo o borrarlo a mano.
    """

    __tablename__ = "fixed_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_movable: Mapped[bool] = mapped_column(default=False)
    source: Mapped[EventSource] = mapped_column(Enum(EventSource), default=EventSource.MANUAL)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship()
