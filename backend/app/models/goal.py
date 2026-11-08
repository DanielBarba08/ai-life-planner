import enum
import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GoalHorizon(str, enum.Enum):
    """Sección 14 del brief original: corto / medio / largo plazo."""

    HOY = "hoy"
    SEMANA = "semana"
    MES = "mes"
    LARGO_PLAZO = "largo_plazo"  # 3–12 meses


class GoalStatus(str, enum.Enum):
    ACTIVO = "activo"
    COMPLETADO = "completado"
    ARCHIVADO = "archivado"


class Goal(Base):
    """
    Objetivo (sección E: goals).

    confirmed_by_user existe desde el MVP aunque hoy siempre sea True,
    porque todo objetivo en este módulo lo crea el usuario directamente.
    Cobra sentido en fases futuras, cuando el asistente pueda *proponer*
    la descomposición de un objetivo en sesiones (punto 14 del brief:
    "NO debe crear objetivos arbitrarios sin confirmación del usuario").
    """

    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    horizon: Mapped[GoalHorizon] = mapped_column(Enum(GoalHorizon), nullable=False)
    status: Mapped[GoalStatus] = mapped_column(Enum(GoalStatus), default=GoalStatus.ACTIVO)
    confirmed_by_user: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship()
    checkins: Mapped[list["GoalCheckin"]] = relationship(back_populates="goal", cascade="all, delete-orphan")


class GoalCheckin(Base):
    """
    Confirmación diaria de un objetivo ("¿cumpliste con tu objetivo hoy?",
    pedido por Daniel el 8 nov para dar racha a los objetivos, igual que ya
    existe para "Mi día" — ver compute_streak en app/planning/service.py).

    Un registro por objetivo y día (`uq_goal_checkins_goal_date`) — a
    diferencia de day_plans, aquí SÍ se guarda explícitamente que el
    usuario dijo que NO cumplió (`completed=False`), porque eso corta la
    racha de inmediato en vez de solo "no abrió la app todavía" (ver
    app/routers/goals.py::_compute_streak, que distingue ambos casos).
    """

    __tablename__ = "goal_checkins"
    __table_args__ = (UniqueConstraint("goal_id", "date", name="uq_goal_checkins_goal_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    goal: Mapped["Goal"] = relationship(back_populates="checkins")
