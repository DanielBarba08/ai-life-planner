"""elimina objetivos (goals/goal_checkins), fusiona en hábitos

Revision ID: 2f19006119ec
Revises: 7a9d60827035
Create Date: 2026-11-12 00:00:00.000000

Daniel pidió eliminar la sección de Objetivos (12 nov): "siento que es
similar a los hábitos". Un hábito ya cubre lo mismo que ofrecía un
objetivo (meta recurrente + progreso real) y además ahora se confirma
solo cada semana (ver app/habits/service.py::auto_confirm_due_sessions),
así que ya no hace falta la versión "ligera" de Goal con check-in manual
y racha aparte.

Orden de borrado por dependencias de FK: primero `habits.goal_id` (su
propia columna, apuntaba a `goals.id`), luego `goal_checkins` (FK a
`goals.id`), y al final `goals`.

No hay forma de migrar datos existentes de un objetivo a un hábito 1:1
en esta migración: Goal no tiene las columnas que Habit exige
(duration_est_min, target_frequency_per_week) y solo el usuario sabe qué
valor le corresponde a cada objetivo suyo. Cualquier objetivo que Daniel
todavía necesite lo recrea a mano como hábito desde Ajustes → Hábitos (o
pidiéndoselo al asistente, que ahora crea hábitos directamente — ver
app/assistant/service.py).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f19006119ec"
down_revision: Union[str, Sequence[str], None] = "7a9d60827035"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("habits", schema=None) as batch_op:
        batch_op.drop_column("goal_id")

    op.drop_index(op.f("ix_goal_checkins_goal_id"), table_name="goal_checkins")
    op.drop_table("goal_checkins")

    op.drop_index(op.f("ix_goals_user_id"), table_name="goals")
    op.drop_table("goals")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "goals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "horizon", sa.Enum("HOY", "SEMANA", "MES", "LARGO_PLAZO", name="goalhorizon"), nullable=False
        ),
        sa.Column(
            "status", sa.Enum("ACTIVO", "COMPLETADO", "ARCHIVADO", name="goalstatus"), nullable=False
        ),
        sa.Column("confirmed_by_user", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"], unique=False)

    op.create_table(
        "goal_checkins",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("goal_id", sa.String(length=36), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("goal_id", "date", name="uq_goal_checkins_goal_date"),
    )
    op.create_index(op.f("ix_goal_checkins_goal_id"), "goal_checkins", ["goal_id"], unique=False)

    with op.batch_alter_table("habits", schema=None) as batch_op:
        batch_op.add_column(sa.Column("goal_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_habits_goal_id", "goals", ["goal_id"], ["id"], ondelete="SET NULL"
        )
