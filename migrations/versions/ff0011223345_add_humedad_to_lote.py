"""add humedad column to lote

Revision ID: ff0011223345
Revises: ff0011223344
Create Date: 2026-05-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ff0011223345'
down_revision: Union[str, None] = 'ff0011223344'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lote', sa.Column('humedad', sa.Numeric(5, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('lote', 'humedad')
