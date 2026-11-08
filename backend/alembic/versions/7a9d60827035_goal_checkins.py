"""goal_checkins (rachas de objetivos)

Revision ID: 7a9d60827035
Revises: fc35c6347bc4
Create Date: 2026-11-08 00:00:00.000000

Tabla `goal_checkins`: confirmación diaria de "¿cumpliste con tu objetivo
hoy?" por objetivo (pedido por Daniel el 8 nov para dar racha a los
objetivos, igual que ya existe para "Mi día" — ver
app/planning/service.py::compute_streak). Un registro por objetivo y día
(uq_goal_checkins_goal_date); a diferencia de day_plans, aquí sí se guarda
explícitamente que el usuario dijo que NO cumplió (completed=False),
porque eso corta la racha de inmediato (ver
app/routers/goals.py::_compute_streak).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a9d60827035"
down_revision: Union[str, Sequence[str], None] = "fc35c6347bc4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
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


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_goal_checkins_goal_id"), table_name="goal_checkins")
    op.drop_table("goal_checkins")
