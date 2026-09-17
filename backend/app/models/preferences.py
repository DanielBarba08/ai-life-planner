import uuid

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserPreferences(Base):
    """
    Preferencias de planificación (sección E: user_preferences).

    Los campos *_hours guardan listas de rangos horarios preferidos, ej.
    [{"start": "09:00", "end": "12:00"}]. Se modelan como JSON en vez de
    tablas separadas porque son datos de configuración de un solo usuario,
    de tamaño acotado, que siempre se leen juntos — una tabla normalizada
    no aportaría nada aquí y sí complejidad de queries.
    """

    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    preferred_focus_hours: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_workout_hours: Mapped[list | None] = mapped_column(JSON, default=list)
    preferred_study_hours: Mapped[list | None] = mapped_column(JSON, default=list)

    # Reglas de descanso: ej. {"min_break_between_blocks_min": 10, "protect_sleep_window": true}
    rest_rules: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Actividades que el usuario NO quiere en ciertas horas, ej.
    # {"entrenar": ["22:00-23:59"], "trabajo_profundo": ["00:00-07:00"]}
    blocked_hours_by_activity: Mapped[dict | None] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="preferences")
