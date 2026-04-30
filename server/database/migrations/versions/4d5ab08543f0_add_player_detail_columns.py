"""add_player_detail_columns

Revision ID: 4d5ab08543f0
Revises: a19785bd241b
Create Date: 2026-01-06 20:54:00.583070

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d5ab08543f0'
down_revision: Union[str, None] = 'a19785bd241b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    columns_to_add = ['health', 'xp_level', 'position_x', 'position_y', 'position_z']
    
    cols_to_create = []
    for col in columns_to_add:
        exists = conn.execute(sa.text(
            f"SELECT 1 FROM information_schema.columns WHERE table_name='player_details' AND column_name='{col}'"
        )).fetchone()
        if not exists:
            cols_to_create.append(col)

    if cols_to_create:
        with op.batch_alter_table('player_details', schema=None) as batch_op:
            if 'health' in cols_to_create:
                batch_op.add_column(sa.Column('health', sa.Integer(), nullable=True))
            if 'xp_level' in cols_to_create:
                batch_op.add_column(sa.Column('xp_level', sa.Integer(), nullable=True))
            if 'position_x' in cols_to_create:
                batch_op.add_column(sa.Column('position_x', sa.Integer(), nullable=True))
            if 'position_y' in cols_to_create:
                batch_op.add_column(sa.Column('position_y', sa.Integer(), nullable=True))
            if 'position_z' in cols_to_create:
                batch_op.add_column(sa.Column('position_z', sa.Integer(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    columns_to_drop = ['position_z', 'position_y', 'position_x', 'xp_level', 'health']
    
    cols_to_drop = []
    for col in columns_to_drop:
        exists = conn.execute(sa.text(
            f"SELECT 1 FROM information_schema.columns WHERE table_name='player_details' AND column_name='{col}'"
        )).fetchone()
        if exists:
            cols_to_drop.append(col)
    
    if cols_to_drop:
        with op.batch_alter_table('player_details', schema=None) as batch_op:
            for col in cols_to_drop:
                batch_op.drop_column(col)

