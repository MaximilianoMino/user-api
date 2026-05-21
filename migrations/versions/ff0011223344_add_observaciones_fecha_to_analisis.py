"""add observaciones_generales and fecha_completado to analisis

Revision ID: ff0011223344
Revises: ddeeff778899
Create Date: 2026-05-18 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ff0011223344'
down_revision: Union[str, None] = 'ddeeff778899'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analisis', sa.Column('observaciones_generales', sa.Text(), nullable=True))
    op.add_column('analisis', sa.Column('fecha_completado', sa.DateTime(), nullable=True))
    op.alter_column('analisis', 'plantilla_id', nullable=True)


def downgrade() -> None:
    op.alter_column('analisis', 'plantilla_id', nullable=False)
    op.drop_column('analisis', 'fecha_completado')
    op.drop_column('analisis', 'observaciones_generales')
