"""evidence_sources y FK real en recommendation_explanations

Revision ID: 04bb1ee767bd
Revises: 75efdbb41fc5
Create Date: 2026-09-14 02:33:39.274195

Catálogo curado del Evidence Engine (sección F/E del blueprint). Las tres
filas que inserta esta migración fueron investigadas y verificadas contra
Crossref (crossref.org) antes de escribirse aquí — no son generadas ni
parafraseadas por un modelo de lenguaje. `topic` conecta cada fila con
app/planning/engine.py::_preference_label vía app/planning/evidence.py.
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.planning.evidence_catalog import EVIDENCE_CATALOG


# revision identifiers, used by Alembic.
revision: str = '04bb1ee767bd'
down_revision: Union[str, Sequence[str], None] = '75efdbb41fc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


evidence_sources = sa.table(
    'evidence_sources',
    sa.column('id', sa.String),
    sa.column('topic', sa.String),
    sa.column('claim', sa.Text),
    sa.column('source', sa.String),
    sa.column('authors', sa.String),
    sa.column('year', sa.Integer),
    sa.column('study_type', sa.String),
    sa.column('doi', sa.String),
    sa.column('evidence_level', sa.String),
    sa.column('limitations', sa.Text),
)

# Misma lista que usan las pruebas (ver tests/conftest.py) — una sola fuente
# de verdad para el contenido. bulk_insert escribe directo a la columna sin
# pasar por el Enum de Python, así que evidence_level tiene que ir como el
# NAME del enum ('SOLIDA'), no su value ('solida') — es como SQLAlchemy
# generó el CHECK constraint de esa columna (ver sa.Enum más abajo).
SEED_ROWS = [
    {"id": str(uuid.uuid4()), **row, "evidence_level": row["evidence_level"].upper()} for row in EVIDENCE_CATALOG
]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'evidence_sources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('topic', sa.String(length=50), nullable=False),
        sa.Column('claim', sa.Text(), nullable=False),
        sa.Column('source', sa.String(length=300), nullable=False),
        sa.Column('authors', sa.String(length=300), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('study_type', sa.String(length=120), nullable=False),
        sa.Column('doi', sa.String(length=120), nullable=True),
        sa.Column('evidence_level', sa.Enum('SOLIDA', 'MODERADA', 'LIMITADA', name='evidencelevel'), nullable=False),
        sa.Column('limitations', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evidence_sources_topic'), 'evidence_sources', ['topic'], unique=False)

    op.bulk_insert(evidence_sources, SEED_ROWS)

    # batch_alter_table: SQLite no soporta ALTER TABLE ADD CONSTRAINT
    # directamente, así que reconstruye la tabla por debajo — funciona igual
    # en Postgres, donde sí se traduce a un ALTER TABLE normal.
    with op.batch_alter_table('recommendation_explanations', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_recommendation_explanations_evidence_ref_id',
            'evidence_sources',
            ['evidence_ref_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('recommendation_explanations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_recommendation_explanations_evidence_ref_id', type_='foreignkey')

    op.drop_index(op.f('ix_evidence_sources_topic'), table_name='evidence_sources')
    op.drop_table('evidence_sources')
