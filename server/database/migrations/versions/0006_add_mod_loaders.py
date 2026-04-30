"""Create mod_loaders table for storing mod loader installations

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('mod_loaders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),  # FORGE, FABRIC, PAPER, VANILLA
        sa.Column('minecraft_version', sa.String(), nullable=False),
        sa.Column('loader_version', sa.String(), nullable=True),
        sa.Column('download_url', sa.String(), nullable=True),
        sa.Column('local_path', sa.String(), nullable=True),
        sa.Column('downloaded', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mod_loaders_id'), 'mod_loaders', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_mod_loaders_id'), table_name='mod_loaders')
    op.drop_table('mod_loaders')
