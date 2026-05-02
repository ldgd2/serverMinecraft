"""add missing player details columns

Revision ID: b7e3d1a2c3b4
Revises: 1e9abf7f89b9
Create Date: 2026-05-02 11:03:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7e3d1a2c3b4'
down_revision: Union[str, None] = '1e9abf7f89b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    
    columns = [
        ('country', sa.String(), True),
        ('os', sa.String(), True),
        ('skin_base64', sa.String(), True),
        ('skin_last_update', sa.DateTime(), True)
    ]
    
    for col_name, col_type, is_nullable in columns:
        check = conn.execute(sa.text(
            f"SELECT 1 FROM information_schema.columns WHERE table_name='player_details' AND column_name='{col_name}'"
        )).fetchone()
        if not check:
            op.add_column('player_details', sa.Column(col_name, col_type, nullable=is_nullable))

def downgrade() -> None:
    op.drop_column('player_details', 'skin_last_update')
    op.drop_column('player_details', 'skin_base64')
    op.drop_column('player_details', 'os')
    op.drop_column('player_details', 'country')
