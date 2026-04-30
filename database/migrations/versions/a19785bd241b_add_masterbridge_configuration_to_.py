"""Add MasterBridge configuration to Server model

Revision ID: a19785bd241b
Revises: a7fe27cd1cb7
Create Date: 2026-01-06 18:23:43.407776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a19785bd241b'
down_revision: Union[str, None] = 'a7fe27cd1cb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add MasterBridge configuration columns to servers table
    op.add_column('servers', sa.Column('masterbridge_enabled', sa.Boolean(), nullable=True))
    op.add_column('servers', sa.Column('masterbridge_ip', sa.String(), nullable=True))
    op.add_column('servers', sa.Column('masterbridge_port', sa.Integer(), nullable=True))
    
    # Set default values for existing rows
    op.execute("UPDATE servers SET masterbridge_enabled = 0 WHERE masterbridge_enabled IS NULL")
    op.execute("UPDATE servers SET masterbridge_ip = '127.0.0.1' WHERE masterbridge_ip IS NULL")
    op.execute("UPDATE servers SET masterbridge_port = 8081 WHERE masterbridge_port IS NULL")


def downgrade() -> None:
    # Remove MasterBridge configuration columns
    op.drop_column('servers', 'masterbridge_port')
    op.drop_column('servers', 'masterbridge_ip')
    op.drop_column('servers', 'masterbridge_enabled')
