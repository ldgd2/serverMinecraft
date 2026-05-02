"""merge all heads

Revision ID: 7e01bc31a73a
Revises: b7e3d1a2c3b4
Create Date: 2026-05-02 11:11:12.472360

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e01bc31a73a'
down_revision: Union[str, None] = 'b7e3d1a2c3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
