"""habits (Fase 5 — hábitos avanzados)

Revision ID: 9210c85efbc0
Revises: 16e005952f99
Create Date: 2026-09-14 22:10:00.000000

Tabla `habits` (hábito recurrente, ej. "entrenar 3 veces por semana") +
`tasks.habit_id`, que enlaza cada sesión CONFIRMADA de un hábito a la
tarea real que representa. Nunca se crea una sesión sin que el usuario la
confirme explícitamente (ver app/habits/service.py::confirm_sessions y el
docstring de app/models/habit.py) — esta migración solo agrega el lugar
donde esas confirmaciones quedan registradas, no crea ningún dato.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9210c85efbc0"
down_revision: Union[str, Sequence[str], None] = "16e005952f99"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "habits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_frequency_per_week", sa.Integer(), nullable=False),
        sa.Column("duration_est_min", sa.Integer(), nullable=False),
        # create_type=False: el tipo ENUM 'concentrationlevel' en Postgres ya
        # lo creó la migración de `tasks` (mismo Enum de Python,
        # ConcentrationLevel, reutilizado aquí) — sin este flag, Postgres
        # fallaría con "type concentrationlevel already exists". SQLite no
        # tiene tipos reales (usa un CHECK por columna), así que este flag
        # no le afecta.
        sa.Column(
            "concentration_level",
            sa.Enum("ALTA", "MEDIA", "BAJA", name="concentrationlevel", create_type=False),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("status", sa.Enum("ACTIVO", "PAUSADO", name="habitstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_habits_user_id"), "habits", ["user_id"], unique=False)

    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("habit_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_tasks_habit_id", "habits", ["habit_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_constraint("fk_tasks_habit_id", type_="foreignkey")
        batch_op.drop_column("habit_id")

    op.drop_index(op.f("ix_habits_user_id"), table_name="habits")
    op.drop_table("habits")
