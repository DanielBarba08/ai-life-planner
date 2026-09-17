"""evidencia general: descanso, sueño, priorización

Revision ID: 20d13a6ee95c
Revises: 9210c85efbc0
Create Date: 2026-09-14 23:40:00.000000

Amplía el catálogo del Evidence Engine con tres citas reales investigadas
y verificadas (DOI confirmado — ver app/planning/evidence_catalog.py) que
respaldan reglas GENERALES del motor (nunca comprimir el sueño, siempre
dejar un descanso entre bloques, combinar prioridad y cercanía de fecha
límite) en vez de la colocación de un bloque en particular. No toca el
esquema — solo inserta filas nuevas en `evidence_sources`, la misma tabla
que ya creó 04bb1ee767bd. Solo se insertan estas 3 filas (no todo
EVIDENCE_CATALOG de nuevo) porque las tres primeras ya están en cualquier
base que corrió esa migración.
"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.planning.evidence_catalog import EVIDENCE_CATALOG

# revision identifiers, used by Alembic.
revision: str = "20d13a6ee95c"
down_revision: Union[str, Sequence[str], None] = "9210c85efbc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

evidence_sources = sa.table(
    "evidence_sources",
    sa.column("id", sa.String),
    sa.column("topic", sa.String),
    sa.column("claim", sa.Text),
    sa.column("source", sa.String),
    sa.column("authors", sa.String),
    sa.column("year", sa.Integer),
    sa.column("study_type", sa.String),
    sa.column("doi", sa.String),
    sa.column("evidence_level", sa.String),
    sa.column("limitations", sa.Text),
)

NEW_TOPICS = {"descanso", "sueno", "priorizacion"}
SEED_ROWS = [
    {"id": str(uuid.uuid4()), **row, "evidence_level": row["evidence_level"].upper()}
    for row in EVIDENCE_CATALOG
    if row["topic"] in NEW_TOPICS
]


def upgrade() -> None:
    """Upgrade schema."""
    op.bulk_insert(evidence_sources, SEED_ROWS)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    conn.execute(evidence_sources.delete().where(evidence_sources.c.topic.in_(NEW_TOPICS)))
