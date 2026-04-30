"""Update versions schema

Revision ID: 0008
Revises: 0007
Create Date: 2026-01-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns for detailed version tracking
    op.add_column('versions', sa.Column('loader_type', sa.String(), nullable=True))
    op.add_column('versions', sa.Column('mc_version', sa.String(), nullable=True))
    op.add_column('versions', sa.Column('loader_version', sa.String(), nullable=True))
    op.add_column('versions', sa.Column('local_path', sa.String(), nullable=True))
    op.add_column('versions', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('versions', sa.Column('sha256', sa.String(), nullable=True))
    
    # We allow 'name' and 'type' to stay for backward compatibility or general usage, 
    # but specific logic will use the new columns.


def downgrade() -> None:
    op.drop_column('versions', 'loader_type')
    op.drop_column('versions', 'mc_version')
    op.drop_column('versions', 'loader_version')
    op.drop_column('versions', 'local_path')
    op.drop_column('versions', 'file_size')
    op.drop_column('versions', 'sha256')
