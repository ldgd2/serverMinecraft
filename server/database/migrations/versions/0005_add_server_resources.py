"""Add server fields for mod loader and resources

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to servers table
    op.add_column('servers', sa.Column('mod_loader', sa.String(), nullable=True, server_default='VANILLA'))
    op.add_column('servers', sa.Column('cpu_cores', sa.Float(), nullable=True, server_default='1.0'))
    op.add_column('servers', sa.Column('disk_mb', sa.Integer(), nullable=True, server_default='2048'))
    op.add_column('servers', sa.Column('current_players', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('servers', sa.Column('cpu_usage', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('servers', sa.Column('ram_usage', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('servers', sa.Column('disk_usage', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('servers', 'mod_loader')
    op.drop_column('servers', 'cpu_cores')
    op.drop_column('servers', 'disk_mb')
    op.drop_column('servers', 'current_players')
    op.drop_column('servers', 'cpu_usage')
    op.drop_column('servers', 'ram_usage')
    op.drop_column('servers', 'disk_usage')
