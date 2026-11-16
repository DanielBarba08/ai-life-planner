"""tasks.habit_id pasa de SET NULL a CASCADE

Revision ID: 8c4d2b9a1f3e
Revises: 2f19006119ec
Create Date: 2026-11-16 20:00:00.000000

Antes, al borrar un hábito, sus sesiones confirmadas (tareas reales con
`habit_id` apuntando a él) quedaban huérfanas como tareas normales con el
título congelado del hábito ya borrado — visibles para siempre en Tareas,
sin ninguna señal de que venían de un hábito que ya no existe. Daniel lo
reportó el 16 nov después de borrar un hábito "Leer" y confundir esas
sobras con tareas duplicadas de uno nuevo.

Pedido explícito: al borrar un hábito, sus sesiones se borran con él
(pendientes y completadas por igual) — ver
app/habits/service.py::delete_habit_and_its_sessions, que además borra
las tareas a nivel de aplicación antes de borrar el hábito, porque SQLite
en desarrollo/test no aplica este `ondelete` a menos que se active
`PRAGMA foreign_keys` (que este proyecto no activa). Este cambio de FK es
para que el comportamiento también quede correcto a nivel de base de
datos en Postgres, no solo en la ruta de la aplicación.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c4d2b9a1f3e"
down_revision: Union[str, Sequence[str], None] = "2f19006119ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_constraint("fk_tasks_habit_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_tasks_habit_id", "habits", ["habit_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_constraint("fk_tasks_habit_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_tasks_habit_id", "habits", ["habit_id"], ["id"], ondelete="SET NULL"
        )
