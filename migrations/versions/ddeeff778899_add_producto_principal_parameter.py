"""add producto_principal parameter

Revision ID: ddeeff778899
Revises: aabbccdd1122
Create Date: 2026-05-18 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ddeeff778899'
down_revision: Union[str, None] = 'aabbccdd1122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO parametro (codigo, value_type, unidad_default, activo, created_at, updated_at, created_by, updated_by)
        SELECT 'producto_principal', 'peso', 'gramos', true, now(), now(), 1, 1
        WHERE NOT EXISTS (
            SELECT 1 FROM parametro WHERE codigo = 'producto_principal'
        )
    """))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM parametro WHERE codigo = 'producto_principal'"))
