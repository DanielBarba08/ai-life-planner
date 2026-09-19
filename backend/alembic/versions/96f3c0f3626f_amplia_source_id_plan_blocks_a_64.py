"""amplia_source_id_plan_blocks_a_64

Revision ID: 96f3c0f3626f
Revises: 20d13a6ee95c
Create Date: 2026-09-19 20:09:14.183863

plan_blocks.source_id era VARCHAR(36) (pensado solo para un UUID puro),
pero app/planning/service.py arma el id de un bloque de disponibilidad
como f"availability:{uuid}" (13 + 36 = 49 caracteres). En SQLite (dev y
tests) VARCHAR no se aplica como límite duro, así que nunca se notó;
en Postgres sí, y "Optimizar mi día" tronaba en cuanto el plan incluía
algún bloque de disponibilidad (psycopg.errors.StringDataRightTruncation)
— encontrado en el primer uso real contra producción.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96f3c0f3626f'
down_revision: Union[str, Sequence[str], None] = '20d13a6ee95c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('plan_blocks', schema=None) as batch_op:
        batch_op.alter_column(
            'source_id',
            existing_type=sa.String(length=36),
            type_=sa.String(length=64),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('plan_blocks', schema=None) as batch_op:
        batch_op.alter_column(
            'source_id',
            existing_type=sa.String(length=64),
            type_=sa.String(length=36),
            existing_nullable=False,
        )
