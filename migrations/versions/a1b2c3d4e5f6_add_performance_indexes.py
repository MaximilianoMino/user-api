"""add_performance_indexes

Revision ID: a1b2c3d4e5f6
Revises: df6223b6242d
Create Date: 2026-05-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'df6223b6242d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'idx_usuario_auth_user_id',
        'usuario',
        ['auth_user_id'],
        unique=False
    )
    op.create_index(
        'idx_usuario_org_rol_user_org',
        'usuario_organizacion_rol',
        ['user_id', 'org_id'],
        unique=False
    )
    op.create_index(
        'idx_lote_org_deleted',
        'lote',
        ['org_id', 'deleted_at'],
        unique=False
    )
    op.create_index(
        'idx_muestra_lote_id',
        'muestra',
        ['lote_id'],
        unique=False
    )
    op.create_index(
        'idx_evidencia_muestra_estado',
        'evidencia',
        ['muestra_id', 'estado'],
        unique=False
    )
    op.create_index(
        'idx_lote_documento_lote_id',
        'lote_documento',
        ['lote_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('idx_lote_documento_lote_id', table_name='lote_documento')
    op.drop_index('idx_evidencia_muestra_estado', table_name='evidencia')
    op.drop_index('idx_muestra_lote_id', table_name='muestra')
    op.drop_index('idx_lote_org_deleted', table_name='lote')
    op.drop_index('idx_usuario_org_rol_user_org', table_name='usuario_organizacion_rol')
    op.drop_index('idx_usuario_auth_user_id', table_name='usuario')
