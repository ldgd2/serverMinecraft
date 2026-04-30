"""Create worlds table and server_worlds junction table

Revision ID: 0007
Revises: 0006
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Worlds table - stores world backups
    op.create_table('worlds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('seed', sa.String(), nullable=True),
        sa.Column('original_version', sa.String(), nullable=True),  # Version when created
        sa.Column('last_used_version', sa.String(), nullable=True),  # Last version used
        sa.Column('local_path', sa.String(), nullable=True),  # Path in source/worlds/
        sa.Column('size_mb', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_worlds_id'), 'worlds', ['id'], unique=False)
    
    # Junction table for many-to-many relationship between servers and worlds
    op.create_table('server_worlds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_id', sa.Integer(), sa.ForeignKey('servers.id'), nullable=False),
        sa.Column('world_id', sa.Integer(), sa.ForeignKey('worlds.id'), nullable=False),
        sa.Column('copied_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('server_worlds')
    op.drop_index(op.f('ix_worlds_id'), table_name='worlds')
    op.drop_table('worlds')
