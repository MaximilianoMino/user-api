"""make evidencia muestra_id nullable

Revision ID: aabbccdd1122
Revises: a1b2c3d4e5f6
Create Date: 2026-05-18 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'aabbccdd1122'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('evidencia', 'muestra_id',
                    existing_type=sa.dialects.postgresql.UUID(),
                    nullable=True)


def downgrade() -> None:
    op.alter_column('evidencia', 'muestra_id',
                    existing_type=sa.dialects.postgresql.UUID(),
                    nullable=False)
