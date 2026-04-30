"""Create servers table

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('ram_mb', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, default='OFFLINE'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('online_mode', sa.Boolean(), nullable=True, default=False),
        sa.Column('motd', sa.String(), nullable=True, default='A Minecraft Server'),
        sa.Column('max_players', sa.Integer(), nullable=True, default=20),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('port')
    )
    op.create_index(op.f('ix_servers_id'), 'servers', ['id'], unique=False)
    op.create_index(op.f('ix_servers_name'), 'servers', ['name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_servers_name'), table_name='servers')
    op.drop_index(op.f('ix_servers_id'), table_name='servers')
    op.drop_table('servers')
