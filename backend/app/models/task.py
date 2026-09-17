import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Priority(str, enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class ConcentrationLevel(str, enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class TaskStatus(str, enum.Enum):
    PENDIENTE = "pendiente"
    COMPLETADA = "completada"
    POSPUESTA = "pospuesta"


class Task(Base):
    """
    Tarea (sección E: tasks; sección 9 del brief original: sistema de
    prioridades). Es la unidad principal que el Planning Engine del
    Módulo 3 va a distribuir en el calendario.
    """

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.MEDIA)
    duration_est_min: Mapped[int] = mapped_column(Integer, nullable=False)
    concentration_level: Mapped[ConcentrationLevel] = mapped_column(
        Enum(ConcentrationLevel), default=ConcentrationLevel.MEDIA
    )
    # Texto libre a propósito (ej. "Estudio", "Proyecto personal") — el
    # brief no pide un catálogo cerrado de categorías para el MVP.
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDIENTE)

    # Dependencia simple: una tarea puede depender de otra tarea del mismo
    # usuario. El Planning Engine (Módulo 3) la usará para no programar una
    # tarea antes de que su dependencia esté completada.
    depends_on_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    # Hábitos avanzados (Fase 5): si esta tarea es una sesión confirmada de
    # un hábito recurrente, apunta a él — así se puede contar cuántas
    # sesiones de esta semana ya se confirmaron/completaron sin inventar
    # una tabla de "ocurrencias" nueva (ver app/habits/service.py). SET
    # NULL al borrar el hábito: la tarea ya confirmada sigue siendo tarea
    # real del usuario, solo pierde el vínculo.
    habit_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("habits.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship()
    depends_on: Mapped["Task | None"] = relationship(remote_side=[id])
