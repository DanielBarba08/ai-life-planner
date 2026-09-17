import uuid
from datetime import datetime, time

from sqlalchemy import DateTime, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    """Entidad raíz del modelo de datos (sección E del blueprint)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # IANA timezone name, ej. "America/Mexico_City" — nunca asumir una zona fija.
    timezone: Mapped[str] = mapped_column(String(64), default="America/Mexico_City")

    wake_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    sleep_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    onboarding_completed: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    preferences: Mapped["UserPreferences"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    availability_blocks: Mapped[list["AvailabilityBlock"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
