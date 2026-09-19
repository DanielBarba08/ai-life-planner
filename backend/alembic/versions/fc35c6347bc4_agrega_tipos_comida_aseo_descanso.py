"""agrega_tipos_comida_aseo_descanso

Revision ID: fc35c6347bc4
Revises: 96f3c0f3626f
Create Date: 2026-09-19 21:22:21.201843

Agrega MEAL ("comida"), HYGIENE ("aseo") y REST ("descanso") al enum
AvailabilityType (ver app/models/availability.py) para que el usuario pueda
marcar sus horarios de comida, aseo y descanso como bloques recurrentes —
"Optimizar mi día" ya trata cualquier availability_block como ocupado
(app/planning/service.py::_build_fixed_items), así que no hace falta tocar
el motor de planificación, solo ampliar qué tipos existen.

Solo hace falta tocar Postgres. Ahí `type` es un ENUM nativo, así que hay
que agregar los valores nuevos con ALTER TYPE ... ADD VALUE — no se puede
usar un valor agregado en la MISMA transacción en la que se agrega
(limitación real de Postgres, no un descuido), pero esta migración solo
agrega los valores, no inserta filas, así que no es un problema.

En SQLite no hace falta ninguna migración: desde SQLAlchemy 2.0,
`sa.Enum.create_constraint` es False por default, así que la columna
`type` ahí es un VARCHAR sin CHECK (verificado con
`sa.Enum(...).create_constraint` → False) — SQLite nunca validó los
valores a nivel de base de datos, solo la capa de Python/Pydantic lo hace.
El VARCHAR ya mide 8 (el largo de "PERSONAL", el miembro más largo del
enum viejo) y ningún nombre nuevo (MEAL, HYGIENE, REST) lo supera, así que
tampoco hay que ampliar el ancho de columna.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'fc35c6347bc4'
down_revision: Union[str, Sequence[str], None] = '96f3c0f3626f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        for value in ('MEAL', 'HYGIENE', 'REST'):
            op.execute(f"ALTER TYPE availabilitytype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres no soporta quitar valores de un ENUM nativo (ALTER TYPE ...
    # DROP VALUE no existe) sin recrear el tipo entero y todas las columnas
    # que lo usan — no se hace aquí para no arriesgar datos reales en un
    # downgrade. Si hace falta revertir de verdad, es una limitación
    # conocida, no algo que este downgrade finja resolver.
    pass
