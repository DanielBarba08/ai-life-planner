"""matched_preference_label en recommendation_explanations

Revision ID: 16e005952f99
Revises: 04bb1ee767bd
Create Date: 2026-09-14 03:10:00.000000

Personal Productivity Model (Fase 3 del roadmap): persiste la etiqueta de
ventana preferida ("concentración" | "estudio" | "entrenamiento" | NULL)
que el motor ya calculaba por bloque pero que antes se descartaba justo
después de resolver `evidence_ref_id` (ver app/planning/engine.py y
app/planning/service.py::persist_plan). Sin esta columna no hay forma de
saber, más adelante, en qué ventana preferida cayó cada bloque histórico
— y por lo tanto tampoco de calcular cuántos de esos bloques terminaron
en una tarea completada (app/planning/service.py::compute_personal_stats).

Columna nullable y sin backfill a propósito: los planes generados antes
de esta migración no tienen esta información en ningún lado, así que
quedan en NULL en vez de inventarse un valor — las estadísticas del
Personal Productivity Model solo empiezan a acumularse desde que existe
esta columna en adelante (sección 11 del brief: nunca inventar datos).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "16e005952f99"
down_revision: Union[str, Sequence[str], None] = "04bb1ee767bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("recommendation_explanations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("matched_preference_label", sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("recommendation_explanations", schema=None) as batch_op:
        batch_op.drop_column("matched_preference_label")
